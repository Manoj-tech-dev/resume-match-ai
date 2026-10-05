"""Analysis endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from app.api.deps import AnalysisServiceDep, SettingsDep
from app.core.exceptions import FileTooLargeError
from app.schemas.analysis import AnalysisListResponse, AnalysisRecord, AnalysisSummary, ErrorResponse

router = APIRouter(tags=["analyses"])

_ERRORS = {
    404: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    415: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    502: {"model": ErrorResponse},
}
_CHUNK = 64 * 1024


def _read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Read the upload in chunks, aborting as soon as the size limit is exceeded."""
    buffer = bytearray()
    while chunk := upload.file.read(_CHUNK):
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise FileTooLargeError(f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.")
    return bytes(buffer)


@router.post(
    "/analyze",
    response_model=AnalysisRecord,
    status_code=status.HTTP_201_CREATED,
    responses=_ERRORS,
    summary="Analyze a resume (PDF, Word, PowerPoint, Image, or Text) against a job description",
)
def analyze(
    service: AnalysisServiceDep,
    settings: SettingsDep,
    resume: Annotated[UploadFile, File(description="Resume file (PDF, DOCX, PPTX, Image, or TXT)")],
    job_description: Annotated[str, Form(description="Full job description text")] = "",
) -> AnalysisRecord:
    # Defined as a sync endpoint on purpose: PDF parsing and the LLM call are
    # blocking, so FastAPI runs this in its threadpool instead of the event loop.
    try:
        data = _read_limited(resume, settings.max_upload_size_bytes)
    finally:
        resume.file.close()
    analysis = service.analyze(
        filename=resume.filename,
        content_type=resume.content_type,
        data=data,
        job_description=job_description,
    )
    return AnalysisRecord.model_validate(analysis)


@router.get("/analyses", response_model=AnalysisListResponse, summary="List previous analyses")
def list_analyses(
    service: AnalysisServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AnalysisListResponse:
    items, total = service.list(limit=limit, offset=offset)
    return AnalysisListResponse(
        items=[AnalysisSummary.model_validate(i) for i in items], total=total, limit=limit, offset=offset
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisRecord, responses=_ERRORS, summary="Get an analysis")
def get_analysis(analysis_id: uuid.UUID, service: AnalysisServiceDep) -> AnalysisRecord:
    return AnalysisRecord.model_validate(service.get(str(analysis_id)))


@router.delete(
    "/analyses/{analysis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_ERRORS,
    summary="Delete an analysis",
)
def delete_analysis(analysis_id: uuid.UUID, service: AnalysisServiceDep) -> Response:
    service.delete(str(analysis_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
