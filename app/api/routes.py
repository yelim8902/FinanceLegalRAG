from fastapi import APIRouter

from app.schemas.analysis import MonitorRunResponse, MonitorSummaryResponse
from app.services.monitor_service import MonitorService


router = APIRouter(prefix="/monitor", tags=["monitor"])


@router.post("/run", response_model=MonitorRunResponse)
def run_monitor(include_seen: bool = False) -> MonitorRunResponse:
    service = MonitorService()
    return service.run(include_seen=include_seen)


@router.get("/latest", response_model=MonitorRunResponse)
def get_latest_monitor_result(include_seen: bool = True) -> MonitorRunResponse:
    service = MonitorService()
    return service.run(include_seen=include_seen)


@router.get("/summary", response_model=MonitorSummaryResponse)
def get_monitor_summary(include_seen: bool = True) -> MonitorSummaryResponse:
    service = MonitorService()
    return service.summary(include_seen=include_seen)
