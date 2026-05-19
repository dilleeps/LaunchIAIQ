"""Phase 2+ connector stubs. Each declares its metadata so the UI can list it,
but sync() raises until implemented."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import IntegrationConnector
from .base import BaseConnector


class _Stub(BaseConnector):
    def sync(self, db: Session, connector_row: IntegrationConnector) -> dict[str, Any]:
        self._stamp(db, connector_row, "not_implemented")
        return {"ok": False, "error": f"{self.kind} connector is not implemented yet"}


class VeevaVaultRIMConnector(_Stub):
    kind = "veeva_vault_rim"
    label = "Veeva Vault RIM — regulatory submissions"
    auth = "oauth2"
    phase = 2


class VeevaPromoMatsConnector(_Stub):
    kind = "veeva_promomats"
    label = "Veeva Vault PromoMats — MLR/PRC"
    auth = "oauth2"
    phase = 2


class VeevaCRMConnector(_Stub):
    kind = "veeva_crm"
    label = "Veeva CRM — HCP engagement"
    auth = "salesforce_oauth"
    phase = 2


class IQVIAOCEConnector(_Stub):
    kind = "iqvia_oce"
    label = "IQVIA OCE — HCP engagement (alt)"
    auth = "oauth2"
    phase = 3


class SAPConnector(_Stub):
    kind = "sap_s4"
    label = "SAP S/4HANA — actuals & supply"
    auth = "odata"
    phase = 3


class KeycloakSSOConnector(_Stub):
    kind = "keycloak_sso"
    label = "Keycloak — SAML/OIDC SSO broker"
    auth = "saml_oidc"
    phase = 2


class WorkdayConnector(_Stub):
    kind = "workday"
    label = "Workday — org structure / RACI source"
    auth = "scim"
    phase = 3
