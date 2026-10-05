"""Deterministic, offline analysis provider.

Used automatically when no AI API key is configured. It performs real (if
simple) heuristic analysis — skill matching, keyword coverage, experience
estimation — so results genuinely depend on the uploaded resume and job
description and the full UI can be demonstrated locally.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from app.llm.base import LLMProvider
from app.schemas.analysis import (
    AnalysisResult,
    BulletRewrite,
    InterviewQuestion,
    KeywordAnalysis,
    KeywordMatch,
    ProjectRecommendation,
    ScoreBreakdown,
    SectionAssessment,
    Suggestion,
)
from app.services import text_analysis as ta

WEIGHTS = {"skills": 0.35, "keywords": 0.25, "experience": 0.2, "education": 0.1, "projects": 0.1}

PROJECT_IDEAS: dict[str, tuple[str, str]] = {
    "frontend": ("Production-grade SPA dashboard", "Build a responsive, accessible dashboard with routing, state management, data fetching and component tests, deployed with CI."),
    "backend": ("Scalable REST/GraphQL service", "Design and ship an API with authentication, pagination, caching, OpenAPI docs, integration tests and structured logging."),
    "data": ("End-to-end data pipeline", "Ingest a public dataset, transform it with a scheduled ETL job, model it in a relational warehouse and expose analytics queries."),
    "ml": ("ML model serving project", "Train a model on a real dataset, track experiments, and serve predictions behind an API with monitoring for drift."),
    "cloud": ("Cloud-native deployment", "Deploy a multi-service app to a major cloud using managed services, IAM least privilege and infrastructure-as-code."),
    "devops": ("CI/CD + container platform", "Containerize an app, add a full CI/CD pipeline with tests and security scans, and deploy to Kubernetes with health checks."),
    "mobile": ("Cross-platform mobile app", "Ship a mobile app with offline support, push notifications and automated UI tests."),
    "language": ("Open-source CLI tool", "Write a well-tested command-line tool, publish it as a package and document it thoroughly."),
}

ACTION_VERBS = ("Engineered", "Delivered", "Optimized", "Led", "Automated", "Designed")


class MockProvider(LLMProvider):
    name = "mock"
    model = "heuristic-v1"

    def analyze(self, resume_text: str, job_description: str) -> AnalysisResult:
        jd_skills = ta.find_skills(job_description)
        resume_skills = ta.find_skills(resume_text)
        hard_jd = [s for s in jd_skills if ta.skill_category(s) != "soft"]

        matching = [s for s in jd_skills if s in resume_skills]
        missing = [s for s in jd_skills if s not in resume_skills]
        hard_matching = [s for s in hard_jd if s in resume_skills]
        relevant_tech = hard_matching + [
            s for s in resume_skills if s not in hard_matching and ta.skill_category(s) not in {"soft", "practice"}
        ]

        skills_score = round(100 * len(matching) / len(jd_skills)) if jd_skills else 60
        keyword_analysis = self._keywords(resume_text, job_description, jd_skills, resume_skills)
        experience = self._experience(resume_text, job_description, hard_matching, missing)
        education = self._education(resume_text, job_description)
        projects = self._projects(resume_text, hard_matching)

        breakdown = ScoreBreakdown(
            skills=skills_score,
            experience=experience.score,
            education=education.score,
            projects=projects.score,
            keywords=keyword_analysis.match_rate,
        )
        overall = round(sum(getattr(breakdown, k) * w for k, w in WEIGHTS.items()))

        return AnalysisResult(
            job_title=_job_title(job_description),
            overall_score=overall,
            score_explanation=_explanation(overall, breakdown, matching, missing),
            summary=_summary(overall, matching, missing),
            score_breakdown=breakdown,
            matching_skills=matching,
            missing_skills=missing,
            relevant_technologies=relevant_tech[:15],
            experience=experience,
            education=education,
            projects=projects,
            keyword_analysis=keyword_analysis,
            suggestions=self._suggestions(resume_text, missing, keyword_analysis, breakdown),
            improved_bullets=self._bullets(resume_text, hard_matching),
            recommended_projects=self._recommend_projects(missing, hard_jd),
            interview_questions=self._questions(hard_matching, missing),
        )

    # -- sections ---------------------------------------------------------

    @staticmethod
    def _keywords(resume: str, jd: str, jd_skills: dict[str, int], resume_skills: dict[str, int]) -> KeywordAnalysis:
        items: list[KeywordMatch] = []
        for skill, jd_count in jd_skills.items():
            occurrences = resume_skills.get(skill, 0)
            importance = "high" if jd_count >= 2 else "medium"
            items.append(KeywordMatch(keyword=skill, found=occurrences > 0, importance=importance, occurrences=occurrences))
        skill_words = {w.lower() for s in jd_skills for w in s.split()}
        for word, _ in ta.top_keywords(jd, limit=10, exclude=skill_words):
            occurrences = ta.count_occurrences(word, resume)
            items.append(KeywordMatch(keyword=word, found=occurrences > 0, importance="low", occurrences=occurrences))
        items = items[:20]
        weights = {"high": 3, "medium": 2, "low": 1}
        total = sum(weights[i.importance] for i in items)
        hit = sum(weights[i.importance] for i in items if i.found)
        return KeywordAnalysis(match_rate=round(100 * hit / total) if total else 50, keywords=items)

    @staticmethod
    def _experience(resume: str, jd: str, matching: list[str], missing: list[str]) -> SectionAssessment:
        needed = ta.required_years(jd)
        have = ta.estimate_years(resume, datetime.now(UTC).year)
        strengths: list[str] = []
        gaps: list[str] = []
        if needed is None:
            score = 75 if have >= 1 else 55
            summary = f"The job does not state a required number of years. The resume shows roughly {have:g} year(s) of experience."
        else:
            ratio = min(have / needed, 1.25) if needed else 1
            score = round(min(100, 30 + 60 * ratio))
            summary = f"The role asks for about {needed}+ years; the resume indicates roughly {have:g} year(s)."
            if have >= needed:
                strengths.append(f"Meets the {needed}+ years experience requirement")
            else:
                gaps.append(f"About {max(needed - have, 0):g} year(s) short of the stated {needed}+ year requirement")
        if matching:
            strengths.append(f"Hands-on experience with {', '.join(matching[:4])}")
        for skill in missing[:3]:
            gaps.append(f"No demonstrated professional experience with {skill}")
        if not re.search(r"\d+\s*%|\$\s?\d|\d+x\b", resume):
            gaps.append("Experience bullets lack quantified impact (%, $, scale)")
            score = max(score - 5, 0)
        return SectionAssessment(score=score, summary=summary, strengths=strengths, gaps=gaps)

    @staticmethod
    def _education(resume: str, jd: str) -> SectionAssessment:
        jd_wants = ta.mentions_degree(jd)
        has = ta.mentions_degree(resume)
        cs = bool(re.search(r"computer science|software engineering|information technology|computer engineering", resume, re.I))
        if has and cs:
            score, summary = 90, "Holds a relevant technical degree, which aligns well with the role."
        elif has:
            score, summary = 75, "Holds a degree; relevance to the role could be made more explicit."
        elif jd_wants:
            score, summary = 35, "The job mentions a degree requirement but none was detected on the resume."
        else:
            score, summary = 65, "No formal degree detected; the job does not appear to strictly require one."
        strengths = ["Relevant field of study"] if cs else []
        gaps = [] if has or not jd_wants else ["Degree requirement not evidenced"]
        if re.search(r"certif", resume, re.I):
            strengths.append("Lists professional certifications")
            score = min(score + 5, 100)
        return SectionAssessment(score=score, summary=summary, strengths=strengths, gaps=gaps)

    @staticmethod
    def _projects(resume: str, matching: list[str]) -> SectionAssessment:
        has_section = bool(re.search(r"\bprojects?\b", resume, re.I))
        has_links = bool(re.search(r"github\.com|gitlab\.com|https?://", resume, re.I))
        score = (60 if has_section else 35) + min(len(matching) * 5, 25) + (10 if has_links else 0)
        strengths: list[str] = []
        gaps: list[str] = []
        if has_section:
            strengths.append("Includes a projects section")
        else:
            gaps.append("No dedicated projects section")
        if has_links:
            strengths.append("Provides links to code or live demos")
        else:
            gaps.append("No links to repositories or demos")
        summary = (
            "Projects demonstrate relevant technologies." if has_section and matching
            else "Projects could better showcase the technologies this role requires."
        )
        return SectionAssessment(score=min(score, 100), summary=summary, strengths=strengths, gaps=gaps)

    @staticmethod
    def _suggestions(resume: str, missing: list[str], kw: KeywordAnalysis, b: ScoreBreakdown) -> list[Suggestion]:
        out: list[Suggestion] = []
        hard_missing = [m for m in missing if ta.skill_category(m) != "soft"]
        if hard_missing:
            out.append(Suggestion(
                title="Address missing core skills",
                detail=f"The job emphasizes {', '.join(hard_missing[:5])}. If you have any exposure, add it explicitly; otherwise consider a small project to build evidence.",
                priority="high",
            ))
        missing_kw = [k.keyword for k in kw.keywords if not k.found][:6]
        if missing_kw:
            out.append(Suggestion(
                title="Mirror the job's language",
                detail=f"ATS systems match exact terms. Work these keywords in naturally where truthful: {', '.join(missing_kw)}.",
                priority="high" if kw.match_rate < 50 else "medium",
            ))
        if not re.search(r"\d+\s*%|\$\s?\d|\d+x\b", resume):
            out.append(Suggestion(
                title="Quantify your impact",
                detail="Add metrics to bullets (e.g. 'reduced latency by 40%', 'served 10k daily users') to show measurable results.",
                priority="high",
            ))
        if b.projects < 70:
            out.append(Suggestion(
                title="Strengthen the projects section",
                detail="Add 2-3 projects using the target stack, each with a one-line outcome and a GitHub or demo link.",
                priority="medium",
            ))
        words = len(resume.split())
        if words < 250:
            out.append(Suggestion(title="Add more detail", detail="The resume is quite short; expand on responsibilities, scope and outcomes for recent roles.", priority="medium"))
        elif words > 1100:
            out.append(Suggestion(title="Tighten the resume", detail="The resume is long; trim older or less relevant content to keep it to 1-2 pages.", priority="low"))
        out.append(Suggestion(
            title="Tailor the summary",
            detail="Open with a 2-3 line summary that names the target role and your most relevant skills for this job.",
            priority="medium",
        ))
        out.append(Suggestion(
            title="Keep formatting ATS-friendly",
            detail="Use standard section headings, a single-column layout, and avoid text inside images or tables.",
            priority="low",
        ))
        return out[:8]

    @staticmethod
    def _bullets(resume: str, matching: list[str]) -> list[BulletRewrite]:
        rewrites: list[BulletRewrite] = []
        for i, line in enumerate(ta.bullet_lines(resume, limit=4)):
            body = line.rstrip(".")
            first, _, rest = body.partition(" ")
            if first.lower() in {"worked", "responsible", "helped", "assisted", "did", "was", "involved"}:
                body = rest
                if body.lower().startswith(("on ", "for ", "with ", "in ")):
                    body = body.split(" ", 1)[1] if " " in body else body
            else:
                body = body[0].lower() + body[1:] if body else body
            verb = ACTION_VERBS[i % len(ACTION_VERBS)]
            tech = f" using {matching[i % len(matching)]}" if matching and matching[i % len(matching)].lower() not in body.lower() else ""
            rewrites.append(BulletRewrite(original=line, improved=f"{verb} {body}{tech}, resulting in [X%] improvement in [key metric]."))
        return rewrites

    @staticmethod
    def _recommend_projects(missing: list[str], hard_jd: list[str]) -> list[ProjectRecommendation]:
        targets = [m for m in missing if ta.skill_category(m) != "soft"] or hard_jd
        seen: set[str] = set()
        out: list[ProjectRecommendation] = []
        for skill in targets:
            category = ta.skill_category(skill)
            if category in seen or category not in PROJECT_IDEAS:
                continue
            seen.add(category)
            title, description = PROJECT_IDEAS[category]
            skills = [s for s in targets if ta.skill_category(s) == category][:4]
            out.append(ProjectRecommendation(title=title, description=description, skills=skills))
            if len(out) == 3:
                break
        if not out:
            title, description = PROJECT_IDEAS["backend"]
            out.append(ProjectRecommendation(title=title, description=description, skills=hard_jd[:4]))
        return out

    @staticmethod
    def _questions(matching: list[str], missing: list[str]) -> list[InterviewQuestion]:
        qs: list[InterviewQuestion] = []
        for skill in matching[:4]:
            qs.append(InterviewQuestion(
                question=f"Walk me through a challenging problem you solved using {skill}. What trade-offs did you make?",
                category="technical",
                rationale=f"{skill} is required by the role and listed on your resume.",
            ))
        for skill in [m for m in missing if ta.skill_category(m) != "soft"][:3]:
            qs.append(InterviewQuestion(
                question=f"This role uses {skill}. How would you get productive with it quickly, and what related experience do you have?",
                category="gap",
                rationale=f"{skill} appears in the job description but not on your resume.",
            ))
        qs.extend([
            InterviewQuestion(question="Tell me about a project you are most proud of and the impact it had.", category="experience", rationale="Assesses ownership and measurable impact."),
            InterviewQuestion(question="Describe a time you disagreed with a teammate on a technical decision. How was it resolved?", category="behavioral", rationale="Assesses collaboration and communication."),
            InterviewQuestion(question="How do you ensure the quality and reliability of the code you ship?", category="technical", rationale="Assesses testing and engineering practices."),
        ])
        return qs[:10]


# -- helpers --------------------------------------------------------------

_TITLE_HINT = re.compile(r"(?:job\s*title|position|role)\s*[:\-]\s*(.+)", re.I)
_ROLE_WORDS = re.compile(r"\b(engineer|developer|scientist|analyst|manager|designer|architect|intern|lead|specialist|consultant)\b", re.I)


def _job_title(jd: str) -> str:
    match = _TITLE_HINT.search(jd)
    if match:
        return match.group(1).strip()[:80]
    lines = [ln.strip(" #*-\t") for ln in jd.splitlines() if ln.strip()]
    for line in lines[:5]:
        if _ROLE_WORDS.search(line) and len(line) <= 80:
            return line
    return (lines[0][:60] if lines else "Untitled role") or "Untitled role"


def _band(score: int) -> str:
    if score >= 80:
        return "a strong match"
    if score >= 65:
        return "a good match"
    if score >= 45:
        return "a partial match"
    return "a weak match"


def _explanation(overall: int, b: ScoreBreakdown, matching: list[str], missing: list[str]) -> str:
    parts = {"skills": b.skills, "keywords": b.keywords, "experience": b.experience, "education": b.education, "projects": b.projects}
    best = max(parts, key=parts.get)  # type: ignore[arg-type]
    worst = min(parts, key=parts.get)  # type: ignore[arg-type]
    return (
        f"The resume is {_band(overall)} ({overall}/100). It covers {len(matching)} of "
        f"{len(matching) + len(missing)} skills detected in the job description. "
        f"The strongest area is {best} ({parts[best]}) and the weakest is {worst} ({parts[worst]})."
    )


def _summary(overall: int, matching: list[str], missing: list[str]) -> str:
    strong = ", ".join(matching[:5]) or "few of the required skills"
    gap = ", ".join(missing[:4])
    text = f"Overall this candidate is {_band(overall)} for the role, with demonstrated strength in {strong}."
    if gap:
        text += f" The most important gaps to address are {gap}."
    return text
