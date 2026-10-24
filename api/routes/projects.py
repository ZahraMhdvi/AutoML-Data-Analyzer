import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from api.core.auth import get_current_user
from api.core.datasets import read_bytes
from api.services import project_service


router = APIRouter(prefix="/api/projects", tags=["projects"])


class RenameRequest(BaseModel):
    name: str


class TargetRequest(BaseModel):
    target: str


class AITargetRequest(BaseModel):
    fallback_policy: str = "notify"


class SettingsRequest(BaseModel):
    problem_type: str
    target: Optional[str] = None
    target_mode: Optional[str] = None
    preferences: dict = {}


class RunRequest(SettingsRequest):
    algorithm: str


def _read_upload(file):
    content = file.file.read()
    filename = os.path.basename(file.filename or "dataset.xlsx")
    return filename, content, read_bytes(content, filename)


@router.get("")
def list_projects(user=Depends(get_current_user)):
    return {"projects": project_service.list_projects(user["id"])}


@router.post("")
def create_project(file: UploadFile = File(...), name: str = Form(""), user=Depends(get_current_user)):
    filename, content, df = _read_upload(file)
    project_name = (name or "").strip() or os.path.splitext(filename)[0]
    project_id = project_service.create_project(user["id"], project_name[:120], filename, content, df)
    return {"project": project_service.get_project_detail(user["id"], project_id)}


@router.get("/{project_id}")
def get_project(project_id: int, user=Depends(get_current_user)):
    return {"project": project_service.get_project_detail(user["id"], project_id)}


@router.patch("/{project_id}")
def rename_project(project_id: int, body: RenameRequest, user=Depends(get_current_user)):
    project_service.rename_project(user["id"], project_id, body.name)
    return {"project": project_service.get_project_detail(user["id"], project_id)}


@router.delete("/{project_id}")
def delete_project(project_id: int, user=Depends(get_current_user)):
    project_service.delete_project(user["id"], project_id)
    return {"success": True}


@router.post("/{project_id}/validate-target")
def validate_target(project_id: int, body: TargetRequest, user=Depends(get_current_user)):
    return project_service.validate_target(user["id"], project_id, body.target)


@router.post("/{project_id}/ai-target")
def ai_target(project_id: int, body: Optional[AITargetRequest] = None, user=Depends(get_current_user)):
    policy = body.fallback_policy if body else "notify"
    return project_service.generate_ai_target(user["id"], project_id, fallback_policy=policy)


@router.post("/{project_id}/characteristics")
def characteristics(project_id: int, body: SettingsRequest, user=Depends(get_current_user)):
    return project_service.get_characteristics(user["id"], project_id, body.problem_type, body.target,
                                               body.target_mode)


@router.post("/{project_id}/model-selection")
def model_selection(project_id: int, body: SettingsRequest, user=Depends(get_current_user)):
    return project_service.select_models(user["id"], project_id, body.problem_type, body.target,
                                         body.target_mode, body.preferences)


@router.post("/{project_id}/run")
def run(project_id: int, body: RunRequest, user=Depends(get_current_user)):
    project_service.configure_and_run(user["id"], project_id, body.algorithm, body.problem_type, body.target,
                                      body.target_mode, body.preferences)
    return {"project": project_service.get_project_detail(user["id"], project_id)}


@router.post("/{project_id}/versions")
def add_version(project_id: int, file: UploadFile = File(...), user=Depends(get_current_user)):
    filename, content, df = _read_upload(file)
    version_no = project_service.add_version(user["id"], project_id, filename, content, df)
    return {"version_no": version_no, "project": project_service.get_project_detail(user["id"], project_id)}


@router.delete("/{project_id}/versions/{version_no}")
def delete_version(project_id: int, version_no: int, user=Depends(get_current_user)):
    project_service.delete_latest_version(user["id"], project_id, version_no)
    return {"project": project_service.get_project_detail(user["id"], project_id)}


@router.get("/{project_id}/versions/{version_no}/audit")
def audit(project_id: int, version_no: int, format: str = "json", user=Depends(get_current_user)):
    record = project_service.audit_record(user["id"], project_id, version_no)
    name = f"guidml_project{project_id}_v{version_no}_audit"
    if format == "csv":
        return Response(project_service.audit_csv(record), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{name}.csv"'})
    return Response(project_service.audit_json(record), media_type="application/json",
                    headers={"Content-Disposition": f'attachment; filename="{name}.json"'})
