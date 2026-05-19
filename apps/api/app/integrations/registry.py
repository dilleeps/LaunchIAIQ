from .base import BaseConnector
from .clinicaltrials import ClinicalTrialsConnector
from .cms_open_payments import CMSOpenPaymentsConnector
from .dailymed import DailyMedConnector
from .openfda import OpenFDAConnector
from .stubs import (
    IQVIAOCEConnector,
    KeycloakSSOConnector,
    SAPConnector,
    VeevaCRMConnector,
    VeevaPromoMatsConnector,
    VeevaVaultRIMConnector,
    WorkdayConnector,
)
from .who_gho import WHOGHOConnector


_INSTANCES: list[BaseConnector] = [
    OpenFDAConnector(),
    ClinicalTrialsConnector(),
    DailyMedConnector(),
    WHOGHOConnector(),
    CMSOpenPaymentsConnector(),
    VeevaVaultRIMConnector(),
    VeevaPromoMatsConnector(),
    VeevaCRMConnector(),
    IQVIAOCEConnector(),
    SAPConnector(),
    KeycloakSSOConnector(),
    WorkdayConnector(),
]


CONNECTORS: dict[str, dict] = {
    c.kind: {"label": c.label, "phase": c.phase, "auth": c.auth, "_instance": c}
    for c in _INSTANCES
}


def get_connector(kind: str) -> BaseConnector:
    meta = CONNECTORS.get(kind)
    if not meta:
        raise KeyError(f"Unknown connector kind: {kind}")
    return meta["_instance"]
