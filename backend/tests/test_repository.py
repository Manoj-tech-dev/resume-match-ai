import time

import pytest

from app.db.repository import AnalysisRepository
from app.db.session import Database


@pytest.fixture
def repo(database: Database):
    session_iter = database.session()
    session = next(session_iter)
    yield AnalysisRepository(session)
    session_iter.close()


def _fields(**kw) -> dict:
    data = {
        "resume_filename": "cv.pdf",
        "resume_pages": 1,
        "resume_characters": 1200,
        "job_title": "Engineer",
        "job_description": "Build things",
        "overall_score": 70,
        "provider": "mock",
        "model": "heuristic-v1",
        "result": {"overall_score": 70, "nested": {"list": [1, 2, 3]}},
    }
    data.update(kw)
    return data


def test_create_assigns_id_and_timestamp(repo: AnalysisRepository) -> None:
    created = repo.create(**_fields())
    assert len(created.id) == 36
    assert created.created_at is not None


def test_get_roundtrips_json(repo: AnalysisRepository) -> None:
    created = repo.create(**_fields())
    fetched = repo.get(created.id)
    assert fetched is not None
    assert fetched.result == {"overall_score": 70, "nested": {"list": [1, 2, 3]}}


def test_get_missing_returns_none(repo: AnalysisRepository) -> None:
    assert repo.get("does-not-exist") is None


def test_list_is_newest_first_and_paginated(repo: AnalysisRepository) -> None:
    ids = []
    for i in range(3):
        ids.append(repo.create(**_fields(job_title=f"Role {i}")).id)
        time.sleep(0.01)
    assert [a.id for a in repo.list()] == list(reversed(ids))
    assert [a.id for a in repo.list(limit=1, offset=1)] == [ids[1]]
    assert repo.count() == 3


def test_delete(repo: AnalysisRepository) -> None:
    created = repo.create(**_fields())
    assert repo.delete(created.id) is True
    assert repo.get(created.id) is None
    assert repo.delete(created.id) is False
    assert repo.count() == 0


def test_file_database_persists(tmp_path) -> None:
    url = f"sqlite:///{tmp_path / 'nested' / 'test.db'}"
    db = Database(url)
    db.create_all()
    session_iter = db.session()
    created = AnalysisRepository(next(session_iter)).create(**_fields())
    session_iter.close()
    db.dispose()

    db2 = Database(url)
    session_iter = db2.session()
    assert AnalysisRepository(next(session_iter)).get(created.id) is not None
    session_iter.close()
    db2.dispose()
