"""Tests for the numbering service."""
import pytest

from app.services.numbering_service import (
    format_number,
    format_change_order_number,
    TOOL_MODELS,
    FORMATS,
)


class TestFormatNumber:
    def test_rfi_format(self):
        assert format_number("rfi", 1) == "RFI-001"
        assert format_number("rfi", 42) == "RFI-042"
        assert format_number("rfi", 100) == "RFI-100"

    def test_submittal_format(self):
        assert format_number("submittal", 1, 0) == "001.00"
        assert format_number("submittal", 1, 1) == "001.01"
        assert format_number("submittal", 5, 3) == "005.03"

    def test_submittal_default_revision(self):
        assert format_number("submittal", 1) == "001.00"

    def test_transmittal_format(self):
        assert format_number("transmittal", 1) == "TR-001"
        assert format_number("transmittal", 15) == "TR-015"

    def test_punch_list_format(self):
        assert format_number("punch_list_item", 1) == "PL-001"
        assert format_number("punch_list_item", 99) == "PL-099"

    def test_inspection_format(self):
        assert format_number("inspection", 1) == "INSP-001"
        assert format_number("inspection", 10) == "INSP-010"

    def test_bid_package_format(self):
        assert format_number("bid_package", 1) == "BP-001"

    def test_meeting_format(self):
        assert format_number("meeting", 1) == "MTG-001"
        assert format_number("meeting", 25) == "MTG-025"

    def test_pay_app_format(self):
        assert format_number("pay_app", 1) == "#1"
        assert format_number("pay_app", 3) == "#3"
        assert format_number("pay_app", 12) == "#12"

    def test_unknown_tool_raises(self):
        with pytest.raises(ValueError):
            format_number("unknown_tool", 1)


class TestChangeOrderFormat:
    def test_pco_format(self):
        assert format_change_order_number(1) == "PCO-001"
        assert format_change_order_number(5) == "PCO-005"

    def test_co_format(self):
        assert format_change_order_number(1, is_approved=True) == "CO-001"
        assert format_change_order_number(5, is_approved=True) == "CO-005"


class TestToolModels:
    def test_all_tools_have_models(self):
        expected = ["rfi", "submittal", "transmittal", "change_order",
                    "punch_list_item", "inspection", "bid_package",
                    "meeting", "pay_app"]
        for tool in expected:
            assert tool in TOOL_MODELS, f"Missing model for {tool}"
