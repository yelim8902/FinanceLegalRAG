from app.schemas.regulation import RegulationDocument


class NotificationService:
    def create_message(
        self,
        document: RegulationDocument,
        impact_level: str,
        affected_departments: list[str],
    ) -> str:
        departments = ", ".join(affected_departments)
        return (
            f"[규제 변경 감지/{impact_level}] {document.title} 문서가 모니터링되었습니다. "
            f"{departments}의 검토가 필요합니다."
        )
