from fastapi import APIRouter

from ml_engine.ai.llm_target_service import config_status, get_llm_service


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health():
    return {"status": "ok"}


@router.get("/llm")
def llm_health(probe: bool = True):


    status = config_status()
    service = get_llm_service()
    if service is None:
        return {"status": "NOT_CONFIGURED", "config": status}
    if not probe:
        return {"status": "CONFIGURED", "config": status}
    check = service.health_check()
    return {"status": check["status"] if check["status"] == "OK" else check["error_code"],
            "probe": check, "config": status}
