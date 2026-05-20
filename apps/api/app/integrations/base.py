from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import IntegrationConnector


class BaseConnector(ABC):
    kind: str = ""
    label: str = ""
    auth: str = "api_key"
    phase: int = 1

    @abstractmethod
    def sync(self, db: Session, connector_row: IntegrationConnector) -> dict[str, Any]:
        """Pull data and persist. Must update connector_row.last_sync_at and last_sync_status."""

    def _stamp(self, db: Session, row: IntegrationConnector, status: str) -> None:
        row.last_sync_at = datetime.utcnow()
        # Column is varchar(32) — keep status short so it always fits.
        row.last_sync_status = (status or "")[:32]
        db.commit()
