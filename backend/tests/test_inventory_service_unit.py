"""Focused deterministic tests for inventory units, dimensions, and models."""

import pytest
from pydantic import ValidationError

from models.inventory import InventoryLotInput
from services.inventory_service import (
    allocatable_quantity,
    convert_quantity,
    piece_fits,
    requirement_outstanding,
    roll_area_sqft,
)


def test_unit_conversions_are_deterministic():
    assert convert_quantity(10, "linear_ft", "linear_inches") == 120
    assert convert_quantity(120, "linear_inches", "linear_ft") == 10
    assert convert_quantity(3, "pack", "each", pack_size=12) == 36
    assert convert_quantity(36, "each", "case", pack_size=12) == 3


def test_incompatible_unit_conversion_is_rejected():
    with pytest.raises(ValueError):
        convert_quantity(1, "sqft", "each")


def test_roll_area_and_dimension_fit_require_geometry():
    assert roll_area_sqft(54, 240) == 90
    lot = {"width_inches": 54, "remaining_length_inches": 240}
    assert piece_fits(lot, 48, 200)
    assert piece_fits(lot, 200, 48)  # Rotation is allowed.
    assert not piece_fits(lot, 60, 150)  # Enough area alone is not enough.


def test_sheet_fit_allows_rotation_but_not_oversize():
    sheet = {"sheet_width_inches": 24, "sheet_height_inches": 36}
    assert piece_fits(sheet, 36, 24)
    assert not piece_fits(sheet, 30, 30)


def test_lot_cannot_reserve_more_than_on_hand():
    with pytest.raises(ValidationError):
        InventoryLotInput(item_id="item-1", quantity_on_hand=5, reserved_quantity=6)


def test_lot_quantities_cannot_be_negative():
    with pytest.raises(ValidationError):
        InventoryLotInput(item_id="item-1", quantity_on_hand=-1)


def test_consumed_quantity_is_not_reserved_again():
    requirement = {"required_quantity": 10, "consumed_quantity": 4, "reserved_quantity": 3}
    assert requirement_outstanding(requirement) == 3


def test_allocatable_quantity_preserves_other_job_reservations():
    lot = {"quantity_on_hand": 10, "reserved_quantity": 8}
    assert allocatable_quantity(lot) == 2
    assert allocatable_quantity(lot, reserved_for_requirement=3) == 5
