import unittest

from src.security.authorization import has_permission
from src.storage.institutional_tenancy import select_organization_id


class InstitutionalAuthorizationTests(unittest.TestCase):
    def test_role_permissions_are_explicit_and_read_only_viewers_stay_read_only(self):
        self.assertTrue(has_permission("owner", "members:write"))
        self.assertTrue(has_permission("admin", "data:write"))
        self.assertTrue(has_permission("analyst", "analysis:run"))
        self.assertTrue(has_permission("viewer", "analysis:read"))
        self.assertFalse(has_permission("viewer", "data:write"))
        self.assertFalse(has_permission("viewer", "members:write"))
        self.assertFalse(has_permission("analyst", "keys:write"))

    def test_unknown_roles_and_permissions_are_denied(self):
        self.assertFalse(has_permission("operator", "analysis:read"))
        self.assertFalse(has_permission("admin", "unknown:permission"))


class OrganizationSelectionTests(unittest.TestCase):
    def test_explicit_organization_is_required_when_user_has_multiple(self):
        memberships = [11, 22]

        self.assertEqual(select_organization_id(memberships, 22), 22)
        with self.assertRaises(ValueError):
            select_organization_id(memberships, None)

    def test_single_membership_can_be_selected_implicitly(self):
        self.assertEqual(select_organization_id([11], None), 11)

    def test_requested_organization_must_be_a_membership(self):
        with self.assertRaises(ValueError):
            select_organization_id([11], 22)


if __name__ == "__main__":
    unittest.main()
