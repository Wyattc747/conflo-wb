"""Tests for the permission engine.

Tests cover:
- GC permission matrix for all 4 levels x all tools x key actions
- Sub portal permissions
- Owner portal permissions + visibility config
- Phase-based tool availability
- Conditional access (financial_access, bidding_access)
- Owner/Admin bypass (no assignment needed)
- Cross-portal isolation
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.project import Project
from fastapi import HTTPException

from app.services.permission_engine import (
    FINANCIAL_TOOLS,
    BIDDING_TOOLS,
    GC_MATRIX,
    OWNER_MATRIX,
    PHASE_TOOL_MAP,
    SUB_MATRIX,
    TOOLS,
    check_permission,
    get_matrix_permission,
    get_visible_tools,
    is_tool_visible_to_owner,
)

from tests.conftest import (
    ORG_ID,
    PROJECT_ID,
    ADMIN_USER_ID,
    FIELD_USER_ID,
    SUB_COMPANY_ID,
    OWNER_ACCOUNT_ID,
)


# ============================================================
# MATRIX COMPLETENESS TESTS
# ============================================================

class TestMatrixCompleteness:
    """Verify every tool appears in every matrix."""

    def test_gc_matrix_all_levels_have_all_tools(self):
        for level in ["OWNER_ADMIN", "PRE_CONSTRUCTION", "MANAGEMENT", "USER"]:
            for tool in TOOLS:
                assert tool in GC_MATRIX[level], f"{level} missing {tool}"

    def test_sub_matrix_has_all_tools(self):
        for tool in TOOLS:
            assert tool in SUB_MATRIX, f"SUB_MATRIX missing {tool}"

    def test_owner_matrix_has_all_tools(self):
        for tool in TOOLS:
            assert tool in OWNER_MATRIX, f"OWNER_MATRIX missing {tool}"

    def test_phase_tool_map_has_all_phases(self):
        for phase in ["BIDDING", "BUYOUT", "ACTIVE", "CLOSEOUT", "CLOSED"]:
            assert phase in PHASE_TOOL_MAP, f"Missing phase {phase}"

    def test_phase_tool_map_has_all_tools(self):
        for phase in PHASE_TOOL_MAP:
            for tool in TOOLS:
                assert tool in PHASE_TOOL_MAP[phase], f"{phase} missing {tool}"


# ============================================================
# GC OWNER_ADMIN TESTS
# ============================================================

class TestOwnerAdmin:
    """Owner/Admin has full CRUD on everything."""

    def test_owner_admin_crud_all_tools(self):
        for tool in TOOLS:
            for action in ["create", "read", "update", "delete"]:
                assert get_matrix_permission("gc", "OWNER_ADMIN", tool, action), \
                    f"OWNER_ADMIN should have {action} on {tool}"

    def test_owner_admin_verify_punch_list(self):
        assert get_matrix_permission("gc", "OWNER_ADMIN", "punch_list", "verify")

    def test_owner_admin_approve_change_orders(self):
        assert get_matrix_permission("gc", "OWNER_ADMIN", "change_orders", "approve")

    def test_owner_admin_approve_pay_apps(self):
        assert get_matrix_permission("gc", "OWNER_ADMIN", "pay_apps", "approve")


# ============================================================
# GC PRE_CONSTRUCTION TESTS
# ============================================================

class TestPreConstruction:
    """Pre-Con: CRUD on bid tools + directory read/add, N/A on field/financial tools."""

    def test_precon_crud_bid_packages(self):
        for action in ["create", "read", "update", "delete"]:
            assert get_matrix_permission("gc", "PRE_CONSTRUCTION", "bid_packages", action)

    def test_precon_can_read_add_directory(self):
        assert get_matrix_permission("gc", "PRE_CONSTRUCTION", "directory", "read")
        assert get_matrix_permission("gc", "PRE_CONSTRUCTION", "directory", "create")

    def test_precon_no_access_to_field_tools(self):
        field_tools = ["daily_logs", "rfis", "submittals", "punch_list", "inspections",
                        "budget", "pay_apps", "change_orders", "schedule"]
        for tool in field_tools:
            for action in ["create", "read", "update", "delete"]:
                assert not get_matrix_permission("gc", "PRE_CONSTRUCTION", tool, action), \
                    f"PRE_CONSTRUCTION should NOT have {action} on {tool}"


# ============================================================
# GC MANAGEMENT TESTS
# ============================================================

class TestManagement:
    """Management: CRUD on most tools, can verify punch list."""

    def test_management_crud_most_tools(self):
        crud_tools = ["rfis", "submittals", "change_orders", "schedule", "budget",
                       "pay_apps", "meetings", "todo", "procurement", "look_ahead",
                       "closeout", "directory", "documents", "photos"]
        for tool in crud_tools:
            assert get_matrix_permission("gc", "MANAGEMENT", tool, "read"), \
                f"MANAGEMENT should read {tool}"
            assert get_matrix_permission("gc", "MANAGEMENT", tool, "create"), \
                f"MANAGEMENT should create {tool}"

    def test_management_verify_punch_list(self):
        assert get_matrix_permission("gc", "MANAGEMENT", "punch_list", "verify")

    def test_management_view_only_bid_packages(self):
        assert get_matrix_permission("gc", "MANAGEMENT", "bid_packages", "read")
        assert not get_matrix_permission("gc", "MANAGEMENT", "bid_packages", "create")
        assert not get_matrix_permission("gc", "MANAGEMENT", "bid_packages", "delete")

    def test_management_daily_logs_no_delete(self):
        assert get_matrix_permission("gc", "MANAGEMENT", "daily_logs", "create")
        assert get_matrix_permission("gc", "MANAGEMENT", "daily_logs", "read")
        assert get_matrix_permission("gc", "MANAGEMENT", "daily_logs", "update")
        assert not get_matrix_permission("gc", "MANAGEMENT", "daily_logs", "delete")

    def test_management_transmittals_cr_only(self):
        assert get_matrix_permission("gc", "MANAGEMENT", "transmittals", "create")
        assert get_matrix_permission("gc", "MANAGEMENT", "transmittals", "read")
        assert not get_matrix_permission("gc", "MANAGEMENT", "transmittals", "update")
        assert not get_matrix_permission("gc", "MANAGEMENT", "transmittals", "delete")

    def test_management_drawings_no_delete(self):
        assert get_matrix_permission("gc", "MANAGEMENT", "drawings", "create")
        assert get_matrix_permission("gc", "MANAGEMENT", "drawings", "read")
        assert get_matrix_permission("gc", "MANAGEMENT", "drawings", "update")
        assert not get_matrix_permission("gc", "MANAGEMENT", "drawings", "delete")

    def test_management_inspections_cr_only(self):
        assert get_matrix_permission("gc", "MANAGEMENT", "inspections", "create")
        assert get_matrix_permission("gc", "MANAGEMENT", "inspections", "read")
        assert not get_matrix_permission("gc", "MANAGEMENT", "inspections", "update")
        assert not get_matrix_permission("gc", "MANAGEMENT", "inspections", "delete")


# ============================================================
# GC USER TESTS
# ============================================================

class TestUser:
    """USER level: limited access, conditional on financial/bidding access."""

    def test_user_crud_meetings_todo_procurement(self):
        for tool in ["meetings", "todo", "procurement", "look_ahead"]:
            for action in ["create", "read", "update", "delete"]:
                assert get_matrix_permission("gc", "USER", tool, action), \
                    f"USER should have {action} on {tool}"

    def test_user_no_budget_without_financial(self):
        assert not get_matrix_permission("gc", "USER", "budget", "read")
        assert not get_matrix_permission("gc", "USER", "budget", "create")

    def test_user_no_pay_apps_without_financial(self):
        assert not get_matrix_permission("gc", "USER", "pay_apps", "read")

    def test_user_no_bid_packages_without_bidding(self):
        assert not get_matrix_permission("gc", "USER", "bid_packages", "read")

    def test_user_view_change_orders(self):
        assert get_matrix_permission("gc", "USER", "change_orders", "read")
        assert not get_matrix_permission("gc", "USER", "change_orders", "create")

    def test_user_daily_logs_cru(self):
        assert get_matrix_permission("gc", "USER", "daily_logs", "create")
        assert get_matrix_permission("gc", "USER", "daily_logs", "read")
        assert get_matrix_permission("gc", "USER", "daily_logs", "update")
        assert not get_matrix_permission("gc", "USER", "daily_logs", "delete")

    def test_user_rfis_cr_only(self):
        assert get_matrix_permission("gc", "USER", "rfis", "create")
        assert get_matrix_permission("gc", "USER", "rfis", "read")
        assert not get_matrix_permission("gc", "USER", "rfis", "update")
        assert not get_matrix_permission("gc", "USER", "rfis", "delete")

    def test_user_no_verify_punch_list(self):
        assert not get_matrix_permission("gc", "USER", "punch_list", "verify")

    def test_user_punch_list_cr_only(self):
        assert get_matrix_permission("gc", "USER", "punch_list", "create")
        assert get_matrix_permission("gc", "USER", "punch_list", "read")
        assert not get_matrix_permission("gc", "USER", "punch_list", "update")
        assert not get_matrix_permission("gc", "USER", "punch_list", "delete")

    def test_user_drawings_read_only(self):
        assert get_matrix_permission("gc", "USER", "drawings", "read")
        assert not get_matrix_permission("gc", "USER", "drawings", "create")

    def test_user_directory_read_add(self):
        assert get_matrix_permission("gc", "USER", "directory", "read")
        assert get_matrix_permission("gc", "USER", "directory", "create")
        assert not get_matrix_permission("gc", "USER", "directory", "delete")

    def test_user_schedule_read_update(self):
        assert get_matrix_permission("gc", "USER", "schedule", "read")
        assert get_matrix_permission("gc", "USER", "schedule", "update")
        assert not get_matrix_permission("gc", "USER", "schedule", "create")
        assert not get_matrix_permission("gc", "USER", "schedule", "delete")

    def test_user_submittals_cr_only(self):
        assert get_matrix_permission("gc", "USER", "submittals", "create")
        assert get_matrix_permission("gc", "USER", "submittals", "read")
        assert not get_matrix_permission("gc", "USER", "submittals", "update")
        assert not get_matrix_permission("gc", "USER", "submittals", "delete")

    def test_user_transmittals_cr_only(self):
        assert get_matrix_permission("gc", "USER", "transmittals", "create")
        assert get_matrix_permission("gc", "USER", "transmittals", "read")
        assert not get_matrix_permission("gc", "USER", "transmittals", "update")
        assert not get_matrix_permission("gc", "USER", "transmittals", "delete")

    def test_user_inspections_cr_only(self):
        assert get_matrix_permission("gc", "USER", "inspections", "create")
        assert get_matrix_permission("gc", "USER", "inspections", "read")
        assert not get_matrix_permission("gc", "USER", "inspections", "update")
        assert not get_matrix_permission("gc", "USER", "inspections", "delete")

    def test_user_closeout_read_create(self):
        assert get_matrix_permission("gc", "USER", "closeout", "read")
        assert get_matrix_permission("gc", "USER", "closeout", "create")
        assert not get_matrix_permission("gc", "USER", "closeout", "delete")

    def test_user_documents_cru(self):
        assert get_matrix_permission("gc", "USER", "documents", "create")
        assert get_matrix_permission("gc", "USER", "documents", "read")
        assert get_matrix_permission("gc", "USER", "documents", "update")
        assert not get_matrix_permission("gc", "USER", "documents", "delete")

    def test_user_photos_cr_only(self):
        assert get_matrix_permission("gc", "USER", "photos", "create")
        assert get_matrix_permission("gc", "USER", "photos", "read")
        assert not get_matrix_permission("gc", "USER", "photos", "update")
        assert not get_matrix_permission("gc", "USER", "photos", "delete")


# ============================================================
# SUB PORTAL TESTS
# ============================================================

class TestSubPermissions:
    def test_sub_rfis_create_read(self):
        assert get_matrix_permission("sub", None, "rfis", "read")
        assert get_matrix_permission("sub", None, "rfis", "create")
        assert not get_matrix_permission("sub", None, "rfis", "delete")

    def test_sub_submittals_cr_only(self):
        assert get_matrix_permission("sub", None, "submittals", "create")
        assert get_matrix_permission("sub", None, "submittals", "read")
        assert not get_matrix_permission("sub", None, "submittals", "update")
        assert not get_matrix_permission("sub", None, "submittals", "delete")

    def test_sub_punch_list_no_create_no_verify(self):
        assert get_matrix_permission("sub", None, "punch_list", "read")
        assert get_matrix_permission("sub", None, "punch_list", "update")
        assert not get_matrix_permission("sub", None, "punch_list", "create")
        assert not get_matrix_permission("sub", None, "punch_list", "verify")

    def test_sub_pay_apps_cru(self):
        assert get_matrix_permission("sub", None, "pay_apps", "create")
        assert get_matrix_permission("sub", None, "pay_apps", "read")
        assert get_matrix_permission("sub", None, "pay_apps", "update")

    def test_sub_schedule_read_only(self):
        assert get_matrix_permission("sub", None, "schedule", "read")
        assert not get_matrix_permission("sub", None, "schedule", "create")
        assert not get_matrix_permission("sub", None, "schedule", "update")

    def test_sub_transmittals_read_only(self):
        assert get_matrix_permission("sub", None, "transmittals", "read")
        assert not get_matrix_permission("sub", None, "transmittals", "create")

    def test_sub_todo_crud(self):
        for action in ["create", "read", "update", "delete"]:
            assert get_matrix_permission("sub", None, "todo", action)

    def test_sub_no_budget(self):
        assert not get_matrix_permission("sub", None, "budget", "read")

    def test_sub_no_daily_logs(self):
        assert not get_matrix_permission("sub", None, "daily_logs", "read")

    def test_sub_drawings_read_only(self):
        assert get_matrix_permission("sub", None, "drawings", "read")
        assert not get_matrix_permission("sub", None, "drawings", "create")

    def test_sub_change_orders_read_update(self):
        assert get_matrix_permission("sub", None, "change_orders", "read")
        assert get_matrix_permission("sub", None, "change_orders", "update")
        assert not get_matrix_permission("sub", None, "change_orders", "create")
        assert not get_matrix_permission("sub", None, "change_orders", "delete")

    def test_sub_bid_packages_read_only(self):
        assert get_matrix_permission("sub", None, "bid_packages", "read")
        assert not get_matrix_permission("sub", None, "bid_packages", "create")

    def test_sub_closeout_cr(self):
        assert get_matrix_permission("sub", None, "closeout", "create")
        assert get_matrix_permission("sub", None, "closeout", "read")
        assert not get_matrix_permission("sub", None, "closeout", "update")
        assert not get_matrix_permission("sub", None, "closeout", "delete")

    def test_sub_no_inspections(self):
        assert not get_matrix_permission("sub", None, "inspections", "read")

    def test_sub_no_meetings(self):
        assert not get_matrix_permission("sub", None, "meetings", "read")

    def test_sub_no_procurement(self):
        assert not get_matrix_permission("sub", None, "procurement", "read")

    def test_sub_no_look_ahead(self):
        assert not get_matrix_permission("sub", None, "look_ahead", "read")

    def test_sub_directory_read_only(self):
        assert get_matrix_permission("sub", None, "directory", "read")
        assert not get_matrix_permission("sub", None, "directory", "create")

    def test_sub_documents_read_only(self):
        assert get_matrix_permission("sub", None, "documents", "read")
        assert not get_matrix_permission("sub", None, "documents", "create")

    def test_sub_photos_read_only(self):
        assert get_matrix_permission("sub", None, "photos", "read")
        assert not get_matrix_permission("sub", None, "photos", "create")


# ============================================================
# OWNER PORTAL TESTS
# ============================================================

class TestOwnerPermissions:
    def test_owner_pay_apps_approve(self):
        assert get_matrix_permission("owner", None, "pay_apps", "read")
        assert get_matrix_permission("owner", None, "pay_apps", "approve")

    def test_owner_change_orders_approve(self):
        assert get_matrix_permission("owner", None, "change_orders", "read")
        assert get_matrix_permission("owner", None, "change_orders", "approve")

    def test_owner_schedule_read_only(self):
        assert get_matrix_permission("owner", None, "schedule", "read")
        assert not get_matrix_permission("owner", None, "schedule", "create")

    def test_owner_daily_logs_read(self):
        # Matrix allows read; owner_portal_config controls visibility
        assert get_matrix_permission("owner", None, "daily_logs", "read")

    def test_owner_budget_read(self):
        # Matrix allows read; controlled by show_budget_summary toggle
        assert get_matrix_permission("owner", None, "budget", "read")

    def test_owner_no_inspections(self):
        assert not get_matrix_permission("owner", None, "inspections", "read")

    def test_owner_no_meetings(self):
        assert not get_matrix_permission("owner", None, "meetings", "read")

    def test_owner_closeout_read(self):
        assert get_matrix_permission("owner", None, "closeout", "read")

    def test_owner_directory_read(self):
        assert get_matrix_permission("owner", None, "directory", "read")

    def test_owner_punch_list_read_create(self):
        assert get_matrix_permission("owner", None, "punch_list", "read")
        assert get_matrix_permission("owner", None, "punch_list", "create")
        assert not get_matrix_permission("owner", None, "punch_list", "update")
        assert not get_matrix_permission("owner", None, "punch_list", "delete")

    def test_owner_submittals_read_only(self):
        assert get_matrix_permission("owner", None, "submittals", "read")
        assert not get_matrix_permission("owner", None, "submittals", "create")

    def test_owner_rfis_read_only(self):
        assert get_matrix_permission("owner", None, "rfis", "read")
        assert not get_matrix_permission("owner", None, "rfis", "create")

    def test_owner_drawings_read_only(self):
        assert get_matrix_permission("owner", None, "drawings", "read")
        assert not get_matrix_permission("owner", None, "drawings", "create")

    def test_owner_no_transmittals(self):
        assert not get_matrix_permission("owner", None, "transmittals", "read")

    def test_owner_no_todo(self):
        assert not get_matrix_permission("owner", None, "todo", "read")

    def test_owner_no_procurement(self):
        assert not get_matrix_permission("owner", None, "procurement", "read")

    def test_owner_no_look_ahead(self):
        assert not get_matrix_permission("owner", None, "look_ahead", "read")

    def test_owner_no_bid_packages(self):
        assert not get_matrix_permission("owner", None, "bid_packages", "read")

    def test_owner_no_documents(self):
        assert not get_matrix_permission("owner", None, "documents", "read")

    def test_owner_no_photos(self):
        assert not get_matrix_permission("owner", None, "photos", "read")


class TestOwnerPortalConfig:
    def test_always_visible_tools(self, default_portal_config):
        for tool in ["pay_apps", "change_orders", "closeout", "directory"]:
            assert is_tool_visible_to_owner(default_portal_config, tool)

    def test_default_config_shows_toggled_tools(self, default_portal_config):
        for tool in ["schedule", "submittals", "rfis", "transmittals",
                      "drawings", "punch_list"]:
            assert is_tool_visible_to_owner(default_portal_config, tool)

    def test_default_config_hides_budget_and_daily_logs(self, default_portal_config):
        assert not is_tool_visible_to_owner(default_portal_config, "budget")
        assert not is_tool_visible_to_owner(default_portal_config, "daily_logs")

    def test_restricted_config_hides_schedule(self, restricted_portal_config):
        assert not is_tool_visible_to_owner(restricted_portal_config, "schedule")

    def test_restricted_config_hides_rfis(self, restricted_portal_config):
        assert not is_tool_visible_to_owner(restricted_portal_config, "rfis")

    def test_restricted_config_hides_submittals(self, restricted_portal_config):
        assert not is_tool_visible_to_owner(restricted_portal_config, "submittals")

    def test_restricted_config_hides_drawings(self, restricted_portal_config):
        assert not is_tool_visible_to_owner(restricted_portal_config, "drawings")

    def test_restricted_config_hides_punch_list(self, restricted_portal_config):
        assert not is_tool_visible_to_owner(restricted_portal_config, "punch_list")

    def test_restricted_config_still_shows_pay_apps(self, restricted_portal_config):
        assert is_tool_visible_to_owner(restricted_portal_config, "pay_apps")
        assert is_tool_visible_to_owner(restricted_portal_config, "change_orders")

    def test_restricted_config_still_shows_always_visible(self, restricted_portal_config):
        assert is_tool_visible_to_owner(restricted_portal_config, "closeout")
        assert is_tool_visible_to_owner(restricted_portal_config, "directory")

    def test_unconfigurable_tools_not_visible(self, default_portal_config):
        """Tools not in OWNER_CONFIG_TOOL_MAP and not ALWAYS_VISIBLE are hidden."""
        for tool in ["inspections", "meetings", "todo", "procurement",
                      "look_ahead", "bid_packages", "documents", "photos"]:
            assert not is_tool_visible_to_owner(default_portal_config, tool)


# ============================================================
# PHASE AVAILABILITY TESTS
# ============================================================

class TestPhaseAvailability:
    def test_bidding_bid_packages_active(self):
        assert PHASE_TOOL_MAP["BIDDING"]["bid_packages"] == "active"

    def test_bidding_daily_logs_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["daily_logs"] == "hidden"

    def test_bidding_budget_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["budget"] == "hidden"

    def test_bidding_closeout_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["closeout"] == "hidden"

    def test_bidding_drawings_active(self):
        assert PHASE_TOOL_MAP["BIDDING"]["drawings"] == "active"

    def test_bidding_rfis_limited(self):
        assert PHASE_TOOL_MAP["BIDDING"]["rfis"] == "limited"

    def test_bidding_submittals_limited(self):
        assert PHASE_TOOL_MAP["BIDDING"]["submittals"] == "limited"

    def test_bidding_transmittals_limited(self):
        assert PHASE_TOOL_MAP["BIDDING"]["transmittals"] == "limited"

    def test_bidding_meetings_limited(self):
        assert PHASE_TOOL_MAP["BIDDING"]["meetings"] == "limited"

    def test_bidding_change_orders_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["change_orders"] == "hidden"

    def test_bidding_schedule_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["schedule"] == "hidden"

    def test_bidding_punch_list_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["punch_list"] == "hidden"

    def test_bidding_inspections_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["inspections"] == "hidden"

    def test_bidding_pay_apps_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["pay_apps"] == "hidden"

    def test_bidding_todo_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["todo"] == "hidden"

    def test_bidding_procurement_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["procurement"] == "hidden"

    def test_bidding_look_ahead_hidden(self):
        assert PHASE_TOOL_MAP["BIDDING"]["look_ahead"] == "hidden"

    def test_bidding_directory_active(self):
        assert PHASE_TOOL_MAP["BIDDING"]["directory"] == "active"

    def test_bidding_documents_active(self):
        assert PHASE_TOOL_MAP["BIDDING"]["documents"] == "active"

    def test_bidding_photos_active(self):
        assert PHASE_TOOL_MAP["BIDDING"]["photos"] == "active"

    def test_active_all_tools_active_except_bids_closeout(self):
        for tool in TOOLS:
            avail = PHASE_TOOL_MAP["ACTIVE"][tool]
            if tool == "bid_packages":
                assert avail == "read_only"
            elif tool == "closeout":
                assert avail == "hidden"
            else:
                assert avail == "active", f"ACTIVE phase: {tool} should be active, got {avail}"

    def test_closeout_closeout_tool_active(self):
        assert PHASE_TOOL_MAP["CLOSEOUT"]["closeout"] == "active"

    def test_closeout_bid_packages_read_only(self):
        assert PHASE_TOOL_MAP["CLOSEOUT"]["bid_packages"] == "read_only"

    def test_closeout_most_tools_active(self):
        for tool in TOOLS:
            avail = PHASE_TOOL_MAP["CLOSEOUT"][tool]
            if tool == "bid_packages":
                assert avail == "read_only"
            else:
                assert avail == "active", f"CLOSEOUT: {tool} should be active, got {avail}"

    def test_closed_everything_read_only(self):
        for tool in TOOLS:
            assert PHASE_TOOL_MAP["CLOSED"][tool] == "read_only", \
                f"CLOSED: {tool} should be read_only"

    def test_buyout_bid_packages_read_only(self):
        assert PHASE_TOOL_MAP["BUYOUT"]["bid_packages"] == "read_only"

    def test_buyout_closeout_hidden(self):
        assert PHASE_TOOL_MAP["BUYOUT"]["closeout"] == "hidden"

    def test_buyout_field_tools_active(self):
        for tool in ["daily_logs", "rfis", "submittals", "punch_list", "schedule"]:
            assert PHASE_TOOL_MAP["BUYOUT"][tool] == "active"

    def test_buyout_financial_tools_active(self):
        for tool in ["budget", "pay_apps", "change_orders"]:
            assert PHASE_TOOL_MAP["BUYOUT"][tool] == "active"

    def test_buyout_communication_tools_active(self):
        for tool in ["meetings", "todo", "procurement", "look_ahead", "transmittals"]:
            assert PHASE_TOOL_MAP["BUYOUT"][tool] == "active"


# ============================================================
# CONDITIONAL ACCESS TESTS
# ============================================================

class TestConditionalAccess:
    """Test USER level conditional access flags."""

    @pytest.mark.asyncio
    async def test_user_denied_budget_without_financial_access(
        self, field_user, active_project, gc_assignment, mock_db
    ):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(field_user, PROJECT_ID, "budget", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_user_allowed_budget_with_financial_access(
        self, field_user, active_project, gc_assignment_financial, mock_db
    ):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment_financial):
            # Should NOT raise
            await check_permission(field_user, PROJECT_ID, "budget", "read", mock_db)

    @pytest.mark.asyncio
    async def test_user_allowed_pay_apps_with_financial_access(
        self, field_user, active_project, gc_assignment_financial, mock_db
    ):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment_financial):
            await check_permission(field_user, PROJECT_ID, "pay_apps", "read", mock_db)

    @pytest.mark.asyncio
    async def test_user_allowed_change_orders_create_with_financial_access(
        self, field_user, active_project, gc_assignment_financial, mock_db
    ):
        """USER normally can only read change_orders; financial_access grants more."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment_financial):
            await check_permission(field_user, PROJECT_ID, "change_orders", "create", mock_db)

    @pytest.mark.asyncio
    async def test_user_denied_bid_packages_without_bidding_access(
        self, field_user, active_project, gc_assignment, mock_db
    ):
        # bid_packages is read_only in ACTIVE phase, and USER has no base permission
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(field_user, PROJECT_ID, "bid_packages", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_user_allowed_bid_packages_with_bidding_access(
        self, field_user, active_project, gc_assignment_bidding, mock_db
    ):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment_bidding):
            await check_permission(field_user, PROJECT_ID, "bid_packages", "read", mock_db)

    @pytest.mark.asyncio
    async def test_financial_access_does_not_grant_bidding(
        self, field_user, active_project, gc_assignment_financial, mock_db
    ):
        """financial_access should not grant access to bid_packages."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment_financial):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(field_user, PROJECT_ID, "bid_packages", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_bidding_access_does_not_grant_financial(
        self, field_user, active_project, gc_assignment_bidding, mock_db
    ):
        """bidding_access should not grant access to budget."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=gc_assignment_bidding):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(field_user, PROJECT_ID, "budget", "read", mock_db)
            assert exc_info.value.status_code == 403


# ============================================================
# OWNER_ADMIN BYPASS TESTS
# ============================================================

class TestOwnerAdminBypass:
    @pytest.mark.asyncio
    async def test_admin_no_assignment_needed(self, admin_user, active_project, mock_db):
        """Owner/Admin can access project without assignment."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            # Should NOT raise
            await check_permission(admin_user, PROJECT_ID, "rfis", "read", mock_db)

    @pytest.mark.asyncio
    async def test_admin_can_create_without_assignment(self, admin_user, active_project, mock_db):
        """Owner/Admin can create on project without assignment."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            await check_permission(admin_user, PROJECT_ID, "rfis", "create", mock_db)

    @pytest.mark.asyncio
    async def test_admin_can_delete_without_assignment(self, admin_user, active_project, mock_db):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            await check_permission(admin_user, PROJECT_ID, "rfis", "delete", mock_db)

    @pytest.mark.asyncio
    async def test_non_admin_denied_without_assignment(self, management_user, active_project, mock_db):
        """Non-admin cannot access project without assignment."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(management_user, PROJECT_ID, "rfis", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_precon_denied_without_assignment(self, precon_user, active_project, mock_db):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(precon_user, PROJECT_ID, "bid_packages", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_field_user_denied_without_assignment(self, field_user, active_project, mock_db):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(field_user, PROJECT_ID, "rfis", "read", mock_db)
            assert exc_info.value.status_code == 403


# ============================================================
# PHASE LOCK TESTS
# ============================================================

class TestPhaseLock:
    @pytest.mark.asyncio
    async def test_closed_project_read_only(self, admin_user, closed_project, mock_db):
        """CLOSED phase: all tools read-only."""
        mock_db.get = AsyncMock(return_value=closed_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            # Read should work
            await check_permission(admin_user, closed_project.id, "rfis", "read", mock_db)
            # Create should fail
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, closed_project.id, "rfis", "create", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_closed_project_no_update(self, admin_user, closed_project, mock_db):
        mock_db.get = AsyncMock(return_value=closed_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, closed_project.id, "submittals", "update", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_closed_project_no_delete(self, admin_user, closed_project, mock_db):
        mock_db.get = AsyncMock(return_value=closed_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, closed_project.id, "daily_logs", "delete", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_bidding_hides_daily_logs(self, admin_user, bidding_project, mock_db):
        """BIDDING phase: daily_logs hidden."""
        mock_db.get = AsyncMock(return_value=bidding_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, bidding_project.id, "daily_logs", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_bidding_hides_closeout(self, admin_user, bidding_project, mock_db):
        mock_db.get = AsyncMock(return_value=bidding_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, bidding_project.id, "closeout", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_bidding_hides_budget(self, admin_user, bidding_project, mock_db):
        mock_db.get = AsyncMock(return_value=bidding_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, bidding_project.id, "budget", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_bidding_hides_pay_apps(self, admin_user, bidding_project, mock_db):
        mock_db.get = AsyncMock(return_value=bidding_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, bidding_project.id, "pay_apps", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_bidding_hides_change_orders(self, admin_user, bidding_project, mock_db):
        mock_db.get = AsyncMock(return_value=bidding_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, bidding_project.id, "change_orders", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_active_hides_closeout(self, admin_user, active_project, mock_db):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, active_project.id, "closeout", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_active_bid_packages_read_only(self, admin_user, active_project, mock_db):
        """In ACTIVE phase, bid_packages is read_only -- read works, create fails."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            await check_permission(admin_user, active_project.id, "bid_packages", "read", mock_db)
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, active_project.id, "bid_packages", "create", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_buyout_closeout_hidden(self, admin_user, buyout_project, mock_db):
        mock_db.get = AsyncMock(return_value=buyout_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(admin_user, buyout_project.id, "closeout", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_closeout_allows_closeout_tool(self, admin_user, closeout_project, mock_db):
        """CLOSEOUT phase: closeout tool is active."""
        mock_db.get = AsyncMock(return_value=closeout_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            await check_permission(admin_user, closeout_project.id, "closeout", "read", mock_db)
            await check_permission(admin_user, closeout_project.id, "closeout", "create", mock_db)


# ============================================================
# CROSS ORG ISOLATION
# ============================================================

class TestCrossOrgIsolation:
    @pytest.mark.asyncio
    async def test_gc_cannot_access_other_org_project(self, admin_user, mock_db):
        """GC user cannot access a project from a different org."""
        other_org_project = MagicMock(spec=Project)
        other_org_project.id = uuid.uuid4()
        other_org_project.organization_id = uuid.uuid4()  # Different org
        other_org_project.phase = "ACTIVE"
        other_org_project.deleted_at = None
        mock_db.get = AsyncMock(return_value=other_org_project)
        with pytest.raises(HTTPException) as exc_info:
            await check_permission(admin_user, other_org_project.id, "rfis", "read", mock_db)
        assert exc_info.value.status_code == 403


# ============================================================
# DELETED PROJECT TESTS
# ============================================================

class TestDeletedProject:
    @pytest.mark.asyncio
    async def test_deleted_project_returns_404(self, admin_user, mock_db):
        """Soft-deleted project should return 404."""
        deleted_project = MagicMock(spec=Project)
        deleted_project.id = uuid.uuid4()
        deleted_project.organization_id = ORG_ID
        deleted_project.phase = "ACTIVE"
        deleted_project.deleted_at = "2025-01-01T00:00:00Z"
        mock_db.get = AsyncMock(return_value=deleted_project)
        with pytest.raises(HTTPException) as exc_info:
            await check_permission(admin_user, deleted_project.id, "rfis", "read", mock_db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_nonexistent_project_returns_404(self, admin_user, mock_db):
        """Project not found should return 404."""
        mock_db.get = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await check_permission(admin_user, uuid.uuid4(), "rfis", "read", mock_db)
        assert exc_info.value.status_code == 404


# ============================================================
# SUB/OWNER ASSIGNMENT TESTS
# ============================================================

class TestSubAssignment:
    @pytest.mark.asyncio
    async def test_sub_denied_without_assignment(self, sub_user, active_project, mock_db):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(sub_user, PROJECT_ID, "rfis", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sub_allowed_with_assignment(self, sub_user, active_project, sub_assignment, mock_db):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=sub_assignment):
            await check_permission(sub_user, PROJECT_ID, "rfis", "read", mock_db)

    @pytest.mark.asyncio
    async def test_sub_denied_action_not_in_matrix(self, sub_user, active_project, sub_assignment, mock_db):
        """Sub cannot delete RFIs even with assignment."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=sub_assignment):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(sub_user, PROJECT_ID, "rfis", "delete", mock_db)
            assert exc_info.value.status_code == 403


class TestOwnerAssignment:
    @pytest.mark.asyncio
    async def test_owner_denied_without_assignment(self, owner_user, active_project, mock_db):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await check_permission(owner_user, PROJECT_ID, "pay_apps", "read", mock_db)
            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_allowed_with_assignment_and_config(
        self, owner_user, active_project, owner_assignment, default_portal_config, mock_db
    ):
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=owner_assignment):
            with patch("app.services.permission_engine.get_owner_portal_config", return_value=default_portal_config):
                await check_permission(owner_user, PROJECT_ID, "pay_apps", "read", mock_db)

    @pytest.mark.asyncio
    async def test_owner_denied_tool_hidden_by_config(
        self, owner_user, active_project, owner_assignment, restricted_portal_config, mock_db
    ):
        """Owner denied if portal config hides the tool."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=owner_assignment):
            with patch("app.services.permission_engine.get_owner_portal_config", return_value=restricted_portal_config):
                with pytest.raises(HTTPException) as exc_info:
                    await check_permission(owner_user, PROJECT_ID, "schedule", "read", mock_db)
                assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_owner_pay_apps_always_visible_despite_restricted_config(
        self, owner_user, active_project, owner_assignment, restricted_portal_config, mock_db
    ):
        """Pay apps are always visible regardless of portal config."""
        mock_db.get = AsyncMock(return_value=active_project)
        with patch("app.services.permission_engine.get_assignment", return_value=owner_assignment):
            with patch("app.services.permission_engine.get_owner_portal_config", return_value=restricted_portal_config):
                await check_permission(owner_user, PROJECT_ID, "pay_apps", "read", mock_db)


# ============================================================
# FINANCIAL/BIDDING TOOL SET TESTS
# ============================================================

class TestToolSets:
    def test_financial_tools_contents(self):
        assert FINANCIAL_TOOLS == {"budget", "pay_apps", "change_orders"}

    def test_bidding_tools_contents(self):
        assert BIDDING_TOOLS == {"bid_packages"}

    def test_tools_list_length(self):
        assert len(TOOLS) == 20

    def test_tools_list_contains_expected(self):
        expected = {
            "daily_logs", "rfis", "submittals", "transmittals", "change_orders",
            "schedule", "drawings", "punch_list", "inspections", "budget",
            "pay_apps", "meetings", "todo", "procurement", "look_ahead",
            "closeout", "bid_packages", "directory", "documents", "photos",
        }
        assert set(TOOLS) == expected


# ============================================================
# get_matrix_permission EDGE CASES
# ============================================================

class TestGetMatrixPermissionEdgeCases:
    def test_unknown_user_type_returns_false(self):
        assert not get_matrix_permission("unknown", None, "rfis", "read")

    def test_unknown_permission_level_returns_false(self):
        assert not get_matrix_permission("gc", "INVALID_LEVEL", "rfis", "read")

    def test_unknown_tool_returns_false(self):
        assert not get_matrix_permission("gc", "OWNER_ADMIN", "nonexistent_tool", "read")

    def test_unknown_action_returns_false(self):
        assert not get_matrix_permission("gc", "OWNER_ADMIN", "rfis", "nonexistent_action")
