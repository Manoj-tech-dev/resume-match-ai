"""Deterministic text-analysis helpers (skill detection, keywords, years of experience).

Used by the mock provider so the app produces meaningful, input-dependent
results without any external AI service.
"""

from __future__ import annotations

import re
from collections import Counter
from functools import lru_cache

# canonical name -> (category, aliases). Aliases are matched case-insensitively.
SKILL_CATALOG: dict[str, tuple[str, tuple[str, ...]]] = {
    # Languages
    "Python": ("language", ("python",)),
    "JavaScript": ("language", ("javascript", "js", "es6")),
    "TypeScript": ("language", ("typescript", "ts")),
    "Java": ("language", ("java",)),
    "C++": ("language", ("c++", "cpp")),
    "C#": ("language", ("c#", "csharp")),
    "Go": ("language", ("golang",)),
    "Rust": ("language", ("rust",)),
    "Ruby": ("language", ("ruby",)),
    "PHP": ("language", ("php",)),
    "Kotlin": ("language", ("kotlin",)),
    "Swift": ("language", ("swift",)),
    "Scala": ("language", ("scala",)),
    "SQL": ("data", ("sql",)),
    "HTML": ("frontend", ("html", "html5")),
    "CSS": ("frontend", ("css", "css3", "sass", "scss")),
    # Frontend
    "React": ("frontend", ("react", "react.js", "reactjs")),
    "Next.js": ("frontend", ("next.js", "nextjs")),
    "Vue": ("frontend", ("vue", "vue.js", "vuejs")),
    "Angular": ("frontend", ("angular",)),
    "Redux": ("frontend", ("redux",)),
    "Tailwind CSS": ("frontend", ("tailwind", "tailwindcss")),
    "React Native": ("mobile", ("react native",)),
    "Flutter": ("mobile", ("flutter",)),
    # Backend
    "Node.js": ("backend", ("node.js", "nodejs", "node")),
    "Express": ("backend", ("express.js", "expressjs")),
    "FastAPI": ("backend", ("fastapi",)),
    "Django": ("backend", ("django",)),
    "Flask": ("backend", ("flask",)),
    "Spring Boot": ("backend", ("spring boot", "spring framework")),
    ".NET": ("backend", (".net", "dotnet", "asp.net")),
    "GraphQL": ("backend", ("graphql",)),
    "REST APIs": ("backend", ("restful", "rest api", "rest apis")),
    "Microservices": ("backend", ("microservices", "microservice")),
    "gRPC": ("backend", ("grpc",)),
    # Data
    "PostgreSQL": ("data", ("postgresql", "postgres")),
    "MySQL": ("data", ("mysql",)),
    "MongoDB": ("data", ("mongodb", "mongo")),
    "Redis": ("data", ("redis",)),
    "Elasticsearch": ("data", ("elasticsearch",)),
    "Kafka": ("data", ("kafka",)),
    "Spark": ("data", ("spark", "pyspark")),
    "Airflow": ("data", ("airflow",)),
    "Pandas": ("data", ("pandas",)),
    "NumPy": ("data", ("numpy",)),
    "Snowflake": ("data", ("snowflake",)),
    "ETL": ("data", ("etl",)),
    # ML / AI
    "Machine Learning": ("ml", ("machine learning", "ml")),
    "Deep Learning": ("ml", ("deep learning",)),
    "TensorFlow": ("ml", ("tensorflow",)),
    "PyTorch": ("ml", ("pytorch",)),
    "scikit-learn": ("ml", ("scikit-learn", "sklearn")),
    "NLP": ("ml", ("nlp", "natural language processing")),
    "LLMs": ("ml", ("llm", "llms", "large language models", "generative ai", "genai")),
    "Computer Vision": ("ml", ("computer vision",)),
    # Cloud / DevOps
    "AWS": ("cloud", ("aws", "amazon web services")),
    "Azure": ("cloud", ("azure",)),
    "GCP": ("cloud", ("gcp", "google cloud")),
    "Docker": ("devops", ("docker",)),
    "Kubernetes": ("devops", ("kubernetes", "k8s")),
    "Terraform": ("devops", ("terraform",)),
    "CI/CD": ("devops", ("ci/cd", "continuous integration", "github actions", "jenkins", "gitlab ci")),
    "Linux": ("devops", ("linux",)),
    "Git": ("tools", ("git", "github", "gitlab")),
    # Practices
    "Unit Testing": ("practice", ("unit testing", "pytest", "jest", "junit", "tdd", "test-driven")),
    "Agile": ("practice", ("agile", "scrum", "kanban")),
    "System Design": ("practice", ("system design", "distributed systems", "scalability")),
    "Data Structures & Algorithms": ("practice", ("data structures", "algorithms")),
    # Soft skills
    "Communication": ("soft", ("communication", "communicate")),
    "Leadership": ("soft", ("leadership", "mentoring", "mentor", "led a team")),
    "Collaboration": ("soft", ("collaboration", "cross-functional", "teamwork")),
    "Problem Solving": ("soft", ("problem solving", "problem-solving")),
}

STOPWORDS = frozenset(
    """a about above across after again against all also am an and any are as at be because been before
    being below between both but by can could did do does doing down during each etc few for from further
    had has have having he her here hers him his how i if in into is it its itself just me more most my no
    nor not now of off on once only or other our ours out over own same she should so some such than that
    the their them then there these they this those through to too under until up very was we were what
    when where which while who whom why will with would you your yours within without per via using use
    able ability strong work working experience experienced years year role team teams company job
    candidate candidates looking join us including include includes required requirements preferred plus
    responsibilities responsible knowledge skills skill understanding good great excellent new well
    across must nice have having etc e.g i.e we're you'll you're will based level related build building
    ensure help across opportunity environment day days time """.split()
)

_TOKEN_RE = re.compile(r"[a-z][a-z0-9+#.\-/]{2,}")


@lru_cache
def _alias_patterns() -> list[tuple[str, re.Pattern[str]]]:
    patterns = []
    for canonical, (_, aliases) in SKILL_CATALOG.items():
        alt = "|".join(re.escape(a) for a in sorted(aliases, key=len, reverse=True))
        patterns.append((canonical, re.compile(rf"(?<![a-z0-9+#.])(?:{alt})(?![a-z0-9+#])")))
    return patterns


def skill_category(skill: str) -> str:
    return SKILL_CATALOG.get(skill, ("other", ()))[0]


def find_skills(text: str) -> dict[str, int]:
    """Return {canonical_skill: occurrences} for skills found in text (order = catalog order)."""
    lowered = text.lower()
    found: dict[str, int] = {}
    for canonical, pattern in _alias_patterns():
        count = len(pattern.findall(lowered))
        if count:
            found[canonical] = count
    return found


def count_occurrences(term: str, text: str) -> int:
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])")
    return len(pattern.findall(text.lower()))


def top_keywords(text: str, limit: int = 12, exclude: set[str] | None = None) -> list[tuple[str, int]]:
    """Most frequent meaningful single-word terms in text."""
    exclude = {e.lower() for e in (exclude or set())}
    tokens = [t.strip(".-/") for t in _TOKEN_RE.findall(text.lower())]
    counts = Counter(t for t in tokens if len(t) > 2 and t not in STOPWORDS and t not in exclude and not t.isdigit())
    return counts.most_common(limit)


_YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)", re.IGNORECASE)
_RANGE_RE = re.compile(
    r"((?:19|20)\d{2})\s*(?:-|–|—|to)\s*((?:19|20)\d{2}|present|current|now)", re.IGNORECASE
)


def required_years(job_description: str) -> int | None:
    values = [int(v) for v in _YEARS_RE.findall(job_description) if 0 < int(v) <= 30]
    return min(values) if values else None


def estimate_years(resume_text: str, current_year: int) -> float:
    """Estimate total experience from explicit 'N years' mentions or date ranges."""
    explicit = [int(v) for v in _YEARS_RE.findall(resume_text) if 0 < int(v) <= 40]
    spans: list[tuple[int, int]] = []
    for start, end in _RANGE_RE.findall(resume_text):
        s = int(start)
        e = current_year if not end[:1].isdigit() else int(end)
        if s <= e <= current_year:
            spans.append((s, e))
    # Merge overlapping spans so concurrent roles aren't double counted.
    total = 0
    for s, e in _merge(spans):
        total += max(e - s, 0)
    return float(max(total, max(explicit, default=0)))


def _merge(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for s, e in sorted(spans):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


DEGREE_TERMS = ("bachelor", "master", "phd", "ph.d", "b.s", "m.s", "b.tech", "m.tech", "b.e", "bsc", "msc", "mba", "degree")


def mentions_degree(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"(?<![a-z]){re.escape(term)}(?![a-z])", lowered) for term in DEGREE_TERMS)


def bullet_lines(resume_text: str, limit: int = 4) -> list[str]:
    """Pick resume lines that look like experience bullets."""
    candidates: list[str] = []
    for line in resume_text.splitlines():
        cleaned = line.strip().lstrip("•●▪◦-*–· ").strip()
        words = cleaned.split()
        if 6 <= len(words) <= 40 and not cleaned.endswith(":") and "@" not in cleaned:
            candidates.append(cleaned)
    # Prefer lines without numbers (they benefit most from quantification).
    candidates.sort(key=lambda c: bool(re.search(r"\d", c)))
    return candidates[:limit]
