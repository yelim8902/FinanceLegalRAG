from fastapi import APIRouter

from app.schemas.compliance import CompanyControl
from app.schemas.analysis import MonitorRunResponse, MonitorSummaryResponse, SeenDocumentRequest
from app.services.compliance_service import ComplianceService
from app.services.monitor_service import MonitorService


router = APIRouter(prefix="/monitor", tags=["monitor"])
company_router = APIRouter(prefix="/company", tags=["company"])


@router.post("/run", response_model=MonitorRunResponse)
def run_monitor(include_seen: bool = False, months_back: int = 1) -> MonitorRunResponse:
    service = MonitorService()
    return service.run(include_seen=include_seen, months_back=months_back)


@router.get("/latest", response_model=MonitorRunResponse)
def get_latest_monitor_result(
    include_seen: bool = True,
    months_back: int = 1,
) -> MonitorRunResponse:
    service = MonitorService()
    return service.run(include_seen=include_seen, months_back=months_back)


@router.get("/summary", response_model=MonitorSummaryResponse)
def get_monitor_summary(
    include_seen: bool = True,
    months_back: int = 1,
) -> MonitorSummaryResponse:
    service = MonitorService()
    return service.summary(include_seen=include_seen, months_back=months_back)


@router.post("/seen")
def mark_document_seen(request: SeenDocumentRequest) -> dict[str, str]:
    service = MonitorService()
    service.mark_seen(request)
    return {"status": "ok"}


@company_router.get("/controls", response_model=list[CompanyControl])
def get_company_controls() -> list[CompanyControl]:
    service = ComplianceService()
    return service.controls
