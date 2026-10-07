import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from api.core.auth import get_current_user
from api.core.datasets import read_bytes, DatasetFileError
from api.services import project_service
from api.services.project_service import WorkflowError
from ml_engine.ai.llm_target_service import LLMTargetServiceError
from ml_engine.model_execution.runner import ModelRunError


router = APIRouter(prefix="/api/projects", tags=["projects"])

logger = logging.getLogger(__name__)


class RenameRequest(BaseModel):
    name: str


class TargetRequest(BaseModel):
    target: str


class SettingsRequest(BaseModel):
    problem_type: str
    target: Optional[str] = None
    target_mode: Optional[str] = None
    preferences: dict = {}


class RunRequest(SettingsRequest):
    algorithm: str


def _user_error(exc):

    if isinstance(exc, HTTPException):
        return exc

    if isinstance(exc, (WorkflowError, DatasetFileError, ModelRunError, LLMTargetServiceError)):
        return HTTPException(400, str(exc))

    logger.exception("Project workflow failed")

    return HTTPException(500, f"خطای غیرمنتظره در پردازش: {exc}")


def _read_upload(file):

    content = file.file.read()
    filename = os.path.basename(file.filename or "dataset.xlsx")

    return filename, content, read_bytes(content, filename)


@router.get("")
def list_projects(user=Depends(get_current_user)):

    return {"projects": project_service.list_projects(user["id"])}


@router.post("")
def create_project(
        file: UploadFile = File(...),
        name: str = Form(""),
        user=Depends(get_current_user)
):

    try:
        filename, content, df = _read_upload(file)

        project_name = (name or "").strip() or os.path.splitext(filename)[0]

        project_id = project_service.create_project(
            user["id"], project_name[:120], filename, content, df
        )

        return {"project": project_service.get_project_detail(user["id"], project_id)}

    except Exception as exc:
        raise _user_error(exc)


@router.get("/{project_id}")
def get_project(project_id: int, user=Depends(get_current_user)):

    return {"project": project_service.get_project_detail(user["id"], project_id)}


@router.patch("/{project_id}")
def rename_project(project_id: int, body: RenameRequest, user=Depends(get_current_user)):

    try:
        project_service.rename_project(user["id"], project_id, body.name)
        return {"project": project_service.get_project_detail(user["id"], project_id)}
    except Exception as exc:
        raise _user_error(exc)


@router.delete("/{project_id}")
def delete_project(project_id: int, user=Depends(get_current_user)):

    project_service.delete_project(user["id"], project_id)

    return {"success": True}


@router.post("/{project_id}/validate-target")
def validate_target(project_id: int, body: TargetRequest, user=Depends(get_current_user)):

    try:
        return project_service.validate_target(user["id"], project_id, body.target)
    except Exception as exc:
        raise _user_error(exc)


@router.post("/{project_id}/ai-target")
def ai_target(project_id: int, user=Depends(get_current_user)):


    from api.routes import ai_target as ai_module

    try:
        return project_service.generate_ai_target(
            user["id"],
            project_id,
            ai_module.llm_service,
            ai_module._build_dataset_profile
        )
    except Exception as exc:
        raise _user_error(exc)


@router.post("/{project_id}/characteristics")
def characteristics(project_id: int, body: SettingsRequest, user=Depends(get_current_user)):

    try:
        return project_service.get_characteristics(
            user["id"], project_id, body.problem_type, body.target, body.target_mode
        )
    except Exception as exc:
        raise _user_error(exc)


@router.post("/{project_id}/model-selection")
def model_selection(project_id: int, body: SettingsRequest, user=Depends(get_current_user)):

    try:
        return project_service.select_models(
            user["id"],
            project_id,
            body.problem_type,
            body.target,
            body.target_mode,
            body.preferences
        )
    except Exception as exc:
        raise _user_error(exc)


@router.post("/{project_id}/run")
def run(project_id: int, body: RunRequest, user=Depends(get_current_user)):

    try:
        project_service.configure_and_run(
            user["id"],
            project_id,
            body.algorithm,
            body.problem_type,
            body.target,
            body.target_mode,
            body.preferences
        )
        return {"project": project_service.get_project_detail(user["id"], project_id)}
    except Exception as exc:
        raise _user_error(exc)


@router.post("/{project_id}/versions")
def add_version(
        project_id: int,
        file: UploadFile = File(...),
        user=Depends(get_current_user)
):

    try:
        filename, content, df = _read_upload(file)

        version_no = project_service.add_version(
            user["id"], project_id, filename, content, df
        )

        return {
            "version_no": version_no,
            "project": project_service.get_project_detail(user["id"], project_id),
        }

    except Exception as exc:
        raise _user_error(exc)


@router.delete("/{project_id}/versions/{version_no}")
def delete_version(project_id: int, version_no: int, user=Depends(get_current_user)):

    try:
        project_service.delete_latest_version(user["id"], project_id, version_no)
        return {"project": project_service.get_project_detail(user["id"], project_id)}
    except Exception as exc:
        raise _user_error(exc)
