import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..integrations.registry import CONNECTORS, get_connector
from ..models import IntegrationConnector, User


router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/available")
def available():
    return [
        {"kind": k, "label": meta["label"], "phase": meta["phase"], "auth": meta["auth"]}
        for k, meta in CONNECTORS.items()
    ]


@router.get("")
def list_conns(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(IntegrationConnector).filter(IntegrationConnector.org_id == user.org_id).all()
    return [
        {
            "id": str(r.id),
            "kind": r.kind,
            "enabled": r.enabled,
            "last_sync_at": r.last_sync_at.isoformat() if r.last_sync_at else None,
            "last_sync_status": r.last_sync_status,
            "config": r.config or {},
        }
        for r in rows
    ]


@router.post("", dependencies=[Depends(require_role("global_admin"))])
def create_conn(
    kind: str,
    config: dict = {},
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if kind not in CONNECTORS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown connector kind")
    conn = IntegrationConnector(org_id=user.org_id, kind=kind, config=config, enabled=True)
    db.add(conn)
    db.commit()
    return {"id": str(conn.id)}


@router.post("/{conn_id}/sync", dependencies=[Depends(require_role("global_admin"))])
def sync(conn_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conn = (
        db.query(IntegrationConnector)
        .filter(IntegrationConnector.id == conn_id, IntegrationConnector.org_id == user.org_id)
        .first()
    )
    if not conn:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connector not found")
    connector = get_connector(conn.kind)
    result = connector.sync(db=db, connector_row=conn)
    return result
