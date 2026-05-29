"""
cross_tenant.py — Parameter contract validator for cross-tenant demo deployments.

Usage
-----
    from src.cross_tenant import validate_cross_tenant_params, CrossTenantParams

    params = CrossTenantParams(
        customer_tenant_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        customer_subscription_id="yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
        customer_region="eastus2",
    )
    errors = validate_cross_tenant_params(params)
    if errors:
        for e in errors:
            print(f"  ✗ {e}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Known Azure regions — used for soft validation (warn, not hard-fail)
# ---------------------------------------------------------------------------
KNOWN_AZURE_REGIONS: frozenset[str] = frozenset(
    [
        "eastus", "eastus2", "westus", "westus2", "westus3",
        "centralus", "northcentralus", "southcentralus",
        "northeurope", "westeurope",
        "uksouth", "ukwest",
        "eastasia", "southeastasia",
        "japaneast", "japanwest",
        "australiaeast", "australiasoutheast",
        "brazilsouth",
        "canadacentral", "canadaeast",
        "francecentral", "francesouth",
        "germanywestcentral",
        "norwayeast",
        "switzerlandnorth",
        "swedencentral",
        "koreacentral", "koreasouth",
        "southafricanorth",
        "uaenorth",
        "centralindia", "southindia", "westindia",
    ]
)

_GUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _is_guid(value: str) -> bool:
    """Return True if *value* looks like a well-formed UUID/GUID."""
    return bool(_GUID_RE.match(value.strip()))


# ---------------------------------------------------------------------------
# Parameter contract
# ---------------------------------------------------------------------------

@dataclass
class CrossTenantParams:
    """All customer-provided values required for a cross-tenant demo deployment.

    Operator-owned values (e.g. ``ENTRA_TENANT_ID``, SQL credentials) come from
    the operator's own ``.env`` / setup run and are *not* included here.

    Attributes
    ----------
    customer_tenant_id:
        Azure AD tenant ID of the customer's directory.  Required for
        cross-tenant deployments.
    customer_subscription_id:
        Azure subscription ID inside the customer tenant to deploy into.
        Required when *customer_tenant_id* is provided.
    customer_app_client_id:
        Client ID of a pre-existing Entra ID app registration in the customer
        tenant.  When supplied, setup skips creating a new app registration.
    customer_app_client_secret:
        Client secret for *customer_app_client_id*.  Required when
        *customer_app_client_id* is provided.
    customer_region:
        Preferred Azure region for resources deployed into the customer
        subscription (e.g. ``"eastus2"``).  Defaults to ``"eastus2"``.
    env_template:
        Optional path to a ``.env`` template file that seeds default values
        before operator-generated values are merged in.
    """

    customer_tenant_id: str = ""
    customer_subscription_id: str = ""
    customer_app_client_id: str = ""
    customer_app_client_secret: str = ""
    customer_region: str = "eastus2"
    env_template: str = ""

    # derived — populated by validate_cross_tenant_params
    warnings: list[str] = field(default_factory=list, repr=False)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate_cross_tenant_params(params: CrossTenantParams) -> list[str]:
    """Validate *params* against the cross-tenant parameter contract.

    Returns a (possibly empty) list of human-readable error strings.
    Warnings are appended to ``params.warnings`` in-place.

    Rules
    -----
    * ``customer_tenant_id`` and ``customer_subscription_id`` are required
      together — you cannot supply one without the other.
    * If either ID is non-empty it must be a valid GUID.
    * If ``customer_app_client_id`` is supplied, ``customer_app_client_secret``
      must also be supplied (and vice-versa).
    * ``customer_region`` must be a non-empty string.  Unknown regions produce
      a warning (not an error) to accommodate new or sovereign regions.
    * ``env_template`` is optional; if provided the path must be a non-empty
      string (actual file-existence checks are left to the caller).
    """
    errors: list[str] = []
    params.warnings = []

    tenant_given = bool(params.customer_tenant_id.strip())
    sub_given = bool(params.customer_subscription_id.strip())

    # Rule: tenant and subscription must be provided together
    if tenant_given and not sub_given:
        errors.append(
            "customer_subscription_id is required when customer_tenant_id is provided"
        )
    if sub_given and not tenant_given:
        errors.append(
            "customer_tenant_id is required when customer_subscription_id is provided"
        )

    # Rule: GUIDs must be well-formed
    if tenant_given and not _is_guid(params.customer_tenant_id):
        errors.append(
            f"customer_tenant_id '{params.customer_tenant_id}' is not a valid GUID "
            "(expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"
        )
    if sub_given and not _is_guid(params.customer_subscription_id):
        errors.append(
            f"customer_subscription_id '{params.customer_subscription_id}' is not a valid GUID"
        )

    # Rule: app registration client ID and secret must be supplied together
    app_id_given = bool(params.customer_app_client_id.strip())
    app_secret_given = bool(params.customer_app_client_secret.strip())
    if app_id_given and not app_secret_given:
        errors.append(
            "customer_app_client_secret is required when customer_app_client_id is provided"
        )
    if app_secret_given and not app_id_given:
        errors.append(
            "customer_app_client_id is required when customer_app_client_secret is provided"
        )
    if app_id_given and not _is_guid(params.customer_app_client_id):
        errors.append(
            f"customer_app_client_id '{params.customer_app_client_id}' is not a valid GUID"
        )

    # Rule: region must be non-empty
    region = params.customer_region.strip()
    if not region:
        errors.append("customer_region must not be empty")
    elif region.lower() not in KNOWN_AZURE_REGIONS:
        params.warnings.append(
            f"customer_region '{region}' is not in the known-regions list; "
            "verify this is a valid Azure region for the customer subscription"
        )

    return errors


def is_cross_tenant_mode(params: CrossTenantParams) -> bool:
    """Return True when *params* configure a cross-tenant deployment."""
    return bool(params.customer_tenant_id.strip() and params.customer_subscription_id.strip())


def env_overrides(params: CrossTenantParams) -> dict[str, str]:
    """Return a dict of env-var overrides derived from *params*.

    These values are written into (or merged into) the ``.env`` file during
    the cross-tenant setup phase so that InfraForge targets the customer
    tenant at runtime.
    """
    overrides: dict[str, str] = {}
    if params.customer_tenant_id.strip():
        overrides["CUSTOMER_TENANT_ID"] = params.customer_tenant_id.strip()
    if params.customer_subscription_id.strip():
        overrides["CUSTOMER_SUBSCRIPTION_ID"] = params.customer_subscription_id.strip()
    if params.customer_app_client_id.strip():
        overrides["CUSTOMER_APP_CLIENT_ID"] = params.customer_app_client_id.strip()
    if params.customer_app_client_secret.strip():
        overrides["CUSTOMER_APP_CLIENT_SECRET"] = params.customer_app_client_secret.strip()
    # Only emit CUSTOMER_REGION when cross-tenant mode is active; the default
    # region value is not meaningful for single-tenant setups.
    if is_cross_tenant_mode(params) and params.customer_region.strip():
        overrides["CUSTOMER_REGION"] = params.customer_region.strip()
    return overrides
