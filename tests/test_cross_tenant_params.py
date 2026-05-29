import unittest

from src.cross_tenant import (
    CrossTenantParams,
    env_overrides,
    is_cross_tenant_mode,
    validate_cross_tenant_params,
)

SAMPLE_TENANT = "aabbccdd-1122-3344-5566-aabbccddeeff"
SAMPLE_SUB = "11223344-aabb-ccdd-eeff-112233445566"
SAMPLE_APP_ID = "deadbeef-dead-beef-dead-beefdeadbeef"
SAMPLE_SECRET = "super-secret-value"


class TestValidateCrossTenantParams(unittest.TestCase):
    # ── Happy paths ───────────────────────────────────────────────────────────

    def test_empty_params_are_valid(self):
        """All fields empty = single-tenant mode; no errors."""
        params = CrossTenantParams()
        self.assertEqual(validate_cross_tenant_params(params), [])

    def test_full_cross_tenant_params_are_valid(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_app_client_id=SAMPLE_APP_ID,
            customer_app_client_secret=SAMPLE_SECRET,
            customer_region="eastus2",
        )
        self.assertEqual(validate_cross_tenant_params(params), [])

    def test_tenant_and_sub_without_app_registration_is_valid(self):
        """Operator can supply tenant+sub and let setup create the app reg."""
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_region="westus2",
        )
        self.assertEqual(validate_cross_tenant_params(params), [])

    def test_unknown_region_produces_warning_not_error(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_region="sovereigncloud-east",
        )
        errors = validate_cross_tenant_params(params)
        self.assertEqual(errors, [])
        self.assertEqual(len(params.warnings), 1)
        self.assertIn("sovereigncloud-east", params.warnings[0])

    def test_known_region_produces_no_warning(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_region="northeurope",
        )
        validate_cross_tenant_params(params)
        self.assertEqual(params.warnings, [])

    # ── Tenant / subscription pairing ────────────────────────────────────────

    def test_tenant_without_subscription_is_error(self):
        params = CrossTenantParams(customer_tenant_id=SAMPLE_TENANT)
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_subscription_id" in e for e in errors))

    def test_subscription_without_tenant_is_error(self):
        params = CrossTenantParams(customer_subscription_id=SAMPLE_SUB)
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_tenant_id" in e for e in errors))

    # ── GUID format validation ────────────────────────────────────────────────

    def test_malformed_tenant_guid_is_error(self):
        params = CrossTenantParams(
            customer_tenant_id="not-a-guid",
            customer_subscription_id=SAMPLE_SUB,
        )
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_tenant_id" in e and "valid GUID" in e for e in errors))

    def test_malformed_subscription_guid_is_error(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id="bad-sub",
        )
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_subscription_id" in e and "valid GUID" in e for e in errors))

    def test_malformed_app_client_id_guid_is_error(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_app_client_id="not-a-guid",
            customer_app_client_secret=SAMPLE_SECRET,
        )
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_app_client_id" in e and "valid GUID" in e for e in errors))

    # ── App registration credential pairing ──────────────────────────────────

    def test_app_client_id_without_secret_is_error(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_app_client_id=SAMPLE_APP_ID,
        )
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_app_client_secret" in e for e in errors))

    def test_app_secret_without_client_id_is_error(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_app_client_secret=SAMPLE_SECRET,
        )
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_app_client_id" in e for e in errors))

    # ── Region validation ─────────────────────────────────────────────────────

    def test_empty_region_is_error(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_region="",
        )
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_region" in e for e in errors))

    def test_whitespace_only_region_is_error(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_region="   ",
        )
        errors = validate_cross_tenant_params(params)
        self.assertTrue(any("customer_region" in e for e in errors))


class TestIsCrossTenantMode(unittest.TestCase):
    def test_empty_params_is_not_cross_tenant(self):
        self.assertFalse(is_cross_tenant_mode(CrossTenantParams()))

    def test_tenant_and_sub_is_cross_tenant(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
        )
        self.assertTrue(is_cross_tenant_mode(params))

    def test_tenant_only_is_not_cross_tenant(self):
        """Both IDs must be present for cross-tenant mode to activate."""
        self.assertFalse(
            is_cross_tenant_mode(CrossTenantParams(customer_tenant_id=SAMPLE_TENANT))
        )


class TestEnvOverrides(unittest.TestCase):
    def test_empty_params_produce_empty_overrides(self):
        self.assertEqual(env_overrides(CrossTenantParams()), {})

    def test_full_params_produce_all_override_keys(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
            customer_app_client_id=SAMPLE_APP_ID,
            customer_app_client_secret=SAMPLE_SECRET,
            customer_region="eastus2",
        )
        overrides = env_overrides(params)
        self.assertEqual(overrides["CUSTOMER_TENANT_ID"], SAMPLE_TENANT)
        self.assertEqual(overrides["CUSTOMER_SUBSCRIPTION_ID"], SAMPLE_SUB)
        self.assertEqual(overrides["CUSTOMER_APP_CLIENT_ID"], SAMPLE_APP_ID)
        self.assertEqual(overrides["CUSTOMER_APP_CLIENT_SECRET"], SAMPLE_SECRET)
        self.assertEqual(overrides["CUSTOMER_REGION"], "eastus2")

    def test_partial_params_only_include_set_keys(self):
        params = CrossTenantParams(
            customer_tenant_id=SAMPLE_TENANT,
            customer_subscription_id=SAMPLE_SUB,
        )
        overrides = env_overrides(params)
        self.assertIn("CUSTOMER_TENANT_ID", overrides)
        self.assertIn("CUSTOMER_SUBSCRIPTION_ID", overrides)
        self.assertNotIn("CUSTOMER_APP_CLIENT_ID", overrides)
        self.assertNotIn("CUSTOMER_APP_CLIENT_SECRET", overrides)

    def test_overrides_strip_whitespace(self):
        params = CrossTenantParams(
            customer_tenant_id=f"  {SAMPLE_TENANT}  ",
            customer_subscription_id=SAMPLE_SUB,
        )
        overrides = env_overrides(params)
        self.assertEqual(overrides["CUSTOMER_TENANT_ID"], SAMPLE_TENANT)


if __name__ == "__main__":
    unittest.main()
