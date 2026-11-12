"""
Security tests for idps (health-facility performance criteria): API rights and row scope.

A criteria evaluates a health facility, so it is visible -- and writable -- when its
health facility is: the user's districts. idps declares no right of its own; it
defaults to the health-facility rights (read 121101, edit 121103).
Tags: [NEW] no reference equivalent (idps is Cameroon specific).

Fixture: create_security_tree("SPID") -> HF1 in D1, HF2 in D2; the users hold D1.

Run: manage.py test idps.test_security_parity --keepdb
"""
import datetime
import json
from unittest import mock

from django.core.cache import cache
from django.db import models
from django.test import TestCase

from core.models.openimis_graphql_test_case import openIMISGraphQLTestCase
from core.test_helpers import (
    create_right_only_user,
    create_security_tree,
    create_test_interactive_user,
    get_test_token,
)
from idps.models import PerformanceCriteria

HF_QUERY = 121101
HF_EDIT = 121103

CRITERIA_GQL = '{ allCriteria { edges { node { period healthFacility { code } } } } }'


# PerformanceCriteria.save() computes its scores with SQL Server-only SQL (DATEADD /
# DATEDIFF), so it cannot run on PostgreSQL. These tests are about rights and scope,
# not scores: fixtures bypass save() and the mutations run with a plain Model.save.
plain_save = mock.patch.object(
    PerformanceCriteria, "save", lambda self, *args, **kwargs: models.Model.save(self, *args, **kwargs))


def _criteria(hf, period):
    return PerformanceCriteria.objects.bulk_create([PerformanceCriteria(
        health_facility=hf, period=period, medecine_availability=1, qualified_personnel=1,
        garbagecan_availability=1, rooms_cleaness=1, waste_separation=1,
        functionals_toilets=1, sterilization_tools=1, is_validated=False, audit_user_id=-1)])[0]


class CriteriaReadTest(openIMISGraphQLTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tree = create_security_tree("SPID")
        cls.reader = create_right_only_user("spid_reader", [HF_QUERY], [cls.tree.d1.id])
        cls.no_right = create_right_only_user("spid_noright", [], [cls.tree.d1.id])
        cls.admin = create_test_interactive_user(username="spid_admin")
        _criteria(cls.tree.hf1, "SPID-1")
        _criteria(cls.tree.hf2, "SPID-2")

    def setUp(self):
        cache.clear()

    def _query(self, user=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {get_test_token(user)}"} if user else {}
        return json.loads(self.query(CRITERIA_GQL, headers=headers).content)

    def _periods(self, content):
        self.assertNotIn("errors", content, content)
        return {e["node"]["period"] for e in content["data"]["allCriteria"]["edges"]
                if e["node"]["period"].startswith("SPID")}

    def test_anonymous_cannot_list_criteria(self):
        content = self._query(None)
        self.assertFalse((content.get("data") or {}).get("allCriteria"))

    def test_user_without_the_right_cannot_list_criteria(self):
        content = self._query(self.no_right)
        self.assertIn("errors", content)
        self.assertFalse((content.get("data") or {}).get("allCriteria"))

    def test_criteria_are_district_scoped(self):
        self.assertEqual({"SPID-1"}, self._periods(self._query(self.reader)))

    def test_control_admin_sees_every_district(self):
        self.assertEqual({"SPID-1", "SPID-2"}, self._periods(self._query(self.admin)))


@plain_save
class CriteriaWriteTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tree = create_security_tree("SPIW")
        cls.editor = create_right_only_user("spiw_editor", [HF_QUERY, HF_EDIT], [cls.tree.d1.id])
        cls.reader = create_right_only_user("spiw_reader", [HF_QUERY], [cls.tree.d1.id])

    def setUp(self):
        cache.clear()

    def _create(self, user, hf, period):
        from idps.schema import CreateCriteriaMutation
        return CreateCriteriaMutation.async_mutate(
            user, period=period, health_facility=hf.id, medecine_availability=1,
            qualified_personnel=1, garbagecan_availability=1, rooms_cleaness=1,
            waste_separation=1, functionals_toilets=1, sterilization_tools=1)

    def _created(self, period):
        return PerformanceCriteria.objects.filter(period=period).exists()

    def test_control_editor_records_criteria_in_own_district(self):
        errors = self._create(self.editor, self.tree.hf1, "SPIW-own")
        self.assertFalse(errors, errors)
        self.assertTrue(self._created("SPIW-own"))

    def test_criteria_for_a_foreign_health_facility_are_refused(self):
        with self.assertRaises(Exception):
            self._create(self.editor, self.tree.hf2, "SPIW-foreign")
        self.assertFalse(self._created("SPIW-foreign"),
                         "criteria recorded on a health facility outside the user's districts")

    def test_user_without_the_edit_right_cannot_record_criteria(self):
        with self.assertRaises(Exception):
            self._create(self.reader, self.tree.hf1, "SPIW-noright")
        self.assertFalse(self._created("SPIW-noright"))

    def test_foreign_criteria_cannot_be_updated(self):
        from idps.schema import UpdateCriteriaMutation
        foreign = _criteria(self.tree.hf2, "SPIW-upd")
        with self.assertRaises(Exception):
            UpdateCriteriaMutation.async_mutate(
                self.editor, id=foreign.id, is_validated=True, date_from=datetime.date(2026, 1, 1))
        self.assertFalse(PerformanceCriteria.objects.get(id=foreign.id).is_validated,
                         "criteria outside the user's districts was validated")


class InvoiceReportClaimsAreScopedTest(TestCase):
    """The idps invoice report reads its claims through Claim.get_queryset, with the caller."""

    @classmethod
    def setUpTestData(cls):
        cls.tree = create_security_tree("SPIR")
        cls.user = create_right_only_user("spir_rep", [131215], [cls.tree.d1.id])

    def test_invoice_report_reads_the_users_claims(self):
        from claim.models import Claim
        from idps.models import invoice_report_query
        users = []
        original = Claim.get_queryset.__func__

        def spy(cls, queryset, user=None, **kwargs):
            users.append(user)
            return original(cls, queryset, user, **kwargs)

        with mock.patch.object(Claim, "get_queryset", classmethod(spy)):
            invoice_report_query(self.user, dateFrom="2026-01-01", dateTo="2026-01-31")
        self.assertTrue(users, "the invoice report read no claim through Claim.get_queryset")
        self.assertTrue(all(u is self.user for u in users))
