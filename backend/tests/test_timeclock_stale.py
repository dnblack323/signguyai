"""Test: stale open shifts are auto-closed on status/record calls."""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient  # noqa: E402
from services.timeclock_service import get_timeclock_status, record_timeclock_action  # noqa: E402


async def main():
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    tenant_id = f"test-tenant-{uuid.uuid4()}"
    employee_id = f"test-emp-{uuid.uuid4()}"

    # Insert a stale "working" shift from 30h ago
    stale_clock_in = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    stale_shift_id = str(uuid.uuid4())
    await db.timeclock_shifts.insert_one({
        "id": stale_shift_id,
        "tenant_id": tenant_id,
        "employee_id": employee_id,
        "date": stale_clock_in[:10],
        "clock_in": stale_clock_in,
        "clock_out": None,
        "break_minutes": 0.0,
        "status": "working",
        "notes": "",
        "source": "time_clock",
        "created_at": stale_clock_in,
        "updated_at": stale_clock_in,
    })

    # Call get_timeclock_status → should auto-close and return not_started
    status = await get_timeclock_status(db, tenant_id, employee_id)
    print("Status after stale cleanup:", status)
    assert status["status"] == "not_started", f"Expected not_started, got {status['status']}"

    closed = await db.timeclock_shifts.find_one({"id": stale_shift_id}, {"_id": 0})
    print("Stale shift after cleanup:", closed["status"], "auto_closed=", closed.get("auto_closed"))
    assert closed["status"] == "finished"
    assert closed.get("auto_closed") is True
    assert closed["clock_out"] is not None

    # Insert a fresh "working" shift from 1h ago → should remain
    fresh_clock_in = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    fresh_shift_id = str(uuid.uuid4())
    await db.timeclock_shifts.insert_one({
        "id": fresh_shift_id,
        "tenant_id": tenant_id,
        "employee_id": employee_id,
        "date": fresh_clock_in[:10],
        "clock_in": fresh_clock_in,
        "clock_out": None,
        "break_minutes": 0.0,
        "status": "working",
        "notes": "",
        "source": "time_clock",
        "created_at": fresh_clock_in,
        "updated_at": fresh_clock_in,
    })
    status = await get_timeclock_status(db, tenant_id, employee_id)
    print("Status with fresh shift:", status)
    assert status["status"] == "working"

    fresh = await db.timeclock_shifts.find_one({"id": fresh_shift_id}, {"_id": 0})
    assert fresh["status"] == "working"

    # Cleanup: end the fresh shift, verify record_timeclock_action still works
    result = await record_timeclock_action(db, tenant_id, employee_id, "end_work")
    print("end_work result:", result["action"])

    # Cleanup test data
    await db.timeclock_shifts.delete_many({"tenant_id": tenant_id})
    await db.timelogs.delete_many({"employee_id": employee_id})

    print("\n✅ All stale-shift auto-close tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
