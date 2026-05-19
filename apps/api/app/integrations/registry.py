from .base import BaseConnector
from .openfda import OpenFDAConnector
from .stubs import (
    ClinicalTrialsConnector,
    DailyMedConnector,
    IQVIAOCEConnector,
    KeycloakSSOConnector,
    SAPConnector,
    VeevaCRMConnector,
    VeevaPromoMatsConnector,
    VeevaVaultRIMConnector,
    WorkdayConnector,
)


_INSTANCES: list[BaseConnector] = [
    OpenFDAConnector(),
    ClinicalTrialsConnector(),
    DailyMedConnector(),
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
