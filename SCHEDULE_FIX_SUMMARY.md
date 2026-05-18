# Employee Schedule Save Bug Fix

## Issue
User reported: "FAILED TO SAVE" error when trying to save employee schedules in the Team tab.

## Root Cause
**API Contract Mismatch** between frontend and backend:

### Frontend was sending (EmployeeSchedule.js):
```javascript
{
  employee_id: "...",
  day_of_week: "monday",  // ❌ Wrong field name
  date: "2026-05-19",     // ❌ Backend doesn't use this
  start_time: "09:00",
  end_time: "17:00",
  is_off: false,          // ❌ Backend doesn't handle this
  notes: "..."
}
```

### Backend expects (routes/employees.py line 1814-1822):
```python
{
  "employee_id": "...",
  "week_start": "2026-05-12",  // ❌ Frontend wasn't sending this!
  "day": "monday",             // ❌ Frontend sent "day_of_week"
  "start_time": "09:00",
  "end_time": "17:00",
  "notes": "..."
}
```

## The Fix

### File: `/app/frontend/src/pages/EmployeeSchedule.js` (Lines 95-117)

**Before:**
```javascript
await axios.post(`${API}/api/payroll/schedule`, {
  employee_id: selectedEmployeeId,
  day_of_week: day.day_of_week,  // ❌ Wrong field name
  date,                           // ❌ Not needed
  start_time: day.start_time || null,
  end_time: day.end_time || null,
  is_off: day.is_off,            // ❌ Not handled by backend
  notes: day.notes || '',
}, { headers: hdr() });
```

**After:**
```javascript
await axios.post(`${API}/api/payroll/schedule`, {
  employee_id: selectedEmployeeId,
  week_start: weekStart,          // ✅ Added - backend needs this
  day: day.day_of_week,           // ✅ Fixed field name
  start_time: day.start_time || '',
  end_time: day.end_time || '',
  notes: day.notes || '',
}, { headers: hdr() });
```

## Changes Made
1. ✅ Changed `day_of_week` → `day` to match backend expectations
2. ✅ Added `week_start` field (was missing completely)
3. ✅ Removed `date` field (backend doesn't use it)
4. ✅ Removed `is_off` field (backend doesn't handle it)
5. ✅ Changed null values to empty strings for consistency
6. ✅ Added error logging for better debugging

## Testing
- ✅ JavaScript linting passed
- ✅ Code compiles without errors
- ✅ Frontend hot reload applied changes automatically

## Expected Behavior After Fix
When users fill out employee schedules in the Team tab and click "Save Schedule":
- ✅ Request will include the correct fields backend expects
- ✅ Backend will successfully save/update the schedule in `employee_schedules` collection
- ✅ Success toast: "Schedule saved"
- ✅ No more "Failed to save schedule" errors

## Backend Logic (For Reference)
Location: `/app/backend/routes/employees.py` lines 1806-1849

The backend:
1. Checks for existing schedule document for that employee + week
2. If exists: Updates the `shifts` object with the new day data
3. If not exists: Creates new schedule document with initial shift
4. Stores data in MongoDB collection: `employee_schedules`

Data structure:
```python
{
  "id": "uuid",
  "tenant_id": "...",
  "employee_id": "...",
  "week_start": "2026-05-12",
  "shifts": {
    "monday": {"start": "09:00", "end": "17:00", "notes": "..."},
    "tuesday": {"start": "09:00", "end": "17:00", "notes": "..."},
    ...
  },
  "created_at": "...",
  "updated_at": "..."
}
```

## User Action
Please test saving employee schedules in the Team tab to confirm the fix works correctly.
