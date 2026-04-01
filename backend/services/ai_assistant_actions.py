"""
AI Assistant Structured Actions

This module provides structured database actions for the AI Assistant.
All actions are:
- Tenant scoped
- Permission checked
- Require confirmation for destructive changes
- Audit logged

Actions supported:
- create_job
- update_job_status
- create_calendar_event
- add_material
- update_material_cost
- create_invoice
- assign_employee
- log_time_entry
- categorize_expense
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from enum import Enum
import uuid

from models import UserInDB, Permission, user_has_permission


# ============== ACTION DEFINITIONS ==============

class ActionType(str, Enum):
    """All supported structured actions"""
    CREATE_ORDER = "create_order"
    CREATE_JOB = "create_job"
    UPDATE_JOB_STATUS = "update_job_status"
    CREATE_CALENDAR_EVENT = "create_calendar_event"
    ADD_MATERIAL = "add_material"
    UPDATE_MATERIAL_COST = "update_material_cost"
    CREATE_INVOICE = "create_invoice"
    ASSIGN_EMPLOYEE = "assign_employee"
    LOG_TIME_ENTRY = "log_time_entry"
    CATEGORIZE_EXPENSE = "categorize_expense"


class ActionStatus(str, Enum):
    """Status of an action request"""
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ActionRequest(BaseModel):
    """Request to execute a structured action"""
    action_type: ActionType
    parameters: Dict[str, Any]
    requires_confirmation: bool = True
    confirmation_message: Optional[str] = None


class ActionResponse(BaseModel):
    """Response from an action execution"""
    action_id: str
    action_type: ActionType
    status: ActionStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confirmation_required: bool = False
    confirmation_message: Optional[str] = None
    audit_id: Optional[str] = None


# ============== PERMISSION MAPPING ==============

ACTION_PERMISSIONS = {
    ActionType.CREATE_ORDER: Permission.JOBS_EDIT,
    ActionType.CREATE_JOB: Permission.JOBS_EDIT,
    ActionType.UPDATE_JOB_STATUS: Permission.JOBS_EDIT,
    ActionType.CREATE_CALENDAR_EVENT: Permission.JOBS_EDIT,  # Calendar tied to jobs
    ActionType.ADD_MATERIAL: Permission.SETTINGS_MANAGE,  # Inventory in settings
    ActionType.UPDATE_MATERIAL_COST: Permission.SETTINGS_MANAGE,
    ActionType.CREATE_INVOICE: Permission.INVOICES_EDIT,
    ActionType.ASSIGN_EMPLOYEE: Permission.EMPLOYEES_MANAGE,
    ActionType.LOG_TIME_ENTRY: Permission.TIME_CLOCK_MANAGE,
    ActionType.CATEGORIZE_EXPENSE: Permission.FINANCIALS_MANAGE,
}


# Actions that modify or delete data require confirmation
DESTRUCTIVE_ACTIONS = {
    ActionType.UPDATE_JOB_STATUS,  # Can mark complete/cancelled
    ActionType.UPDATE_MATERIAL_COST,  # Financial impact
    ActionType.CREATE_INVOICE,  # Financial commitment
    ActionType.ASSIGN_EMPLOYEE,  # Workload change
}


# ============== ACTION HANDLERS ==============

class AIAssistantActions:
    """Handler for AI Assistant structured database actions"""
    
    def __init__(self, db):
        self.db = db
    
    async def check_permission(self, user: UserInDB, action_type: ActionType) -> bool:
        """Check if user has permission for the action"""
        required_permission = ACTION_PERMISSIONS.get(action_type)
        if not required_permission:
            return False
        return user_has_permission(user.role, required_permission)
    
    async def log_audit(
        self,
        tenant_id: str,
        user_id: str,
        action_type: ActionType,
        action_id: str,
        parameters: Dict[str, Any],
        status: ActionStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> str:
        """Log action to audit table"""
        audit_entry = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "user_id": user_id,
            "action_id": action_id,
            "action_type": action_type.value,
            "parameters": parameters,
            "status": status.value,
            "result": result,
            "error": error,
            "source": "ai_assistant",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.db.ai_action_audit.insert_one(audit_entry)
        return audit_entry["id"]
    
    async def execute_action(
        self,
        user: UserInDB,
        action_request: ActionRequest,
        confirmed: bool = False
    ) -> ActionResponse:
        """Execute a structured action"""
        action_id = str(uuid.uuid4())
        action_type = action_request.action_type
        parameters = action_request.parameters
        
        # Check permission
        if not await self.check_permission(user, action_type):
            audit_id = await self.log_audit(
                user.tenant_id, user.id, action_type, action_id,
                parameters, ActionStatus.FAILED, error="Permission denied"
            )
            return ActionResponse(
                action_id=action_id,
                action_type=action_type,
                status=ActionStatus.FAILED,
                error=f"Permission denied: You do not have permission to {action_type.value}",
                audit_id=audit_id
            )
        
        # Check if confirmation required
        is_destructive = action_type in DESTRUCTIVE_ACTIONS
        if is_destructive and not confirmed:
            confirmation_msg = self._get_confirmation_message(action_type, parameters)
            audit_id = await self.log_audit(
                user.tenant_id, user.id, action_type, action_id,
                parameters, ActionStatus.PENDING_CONFIRMATION
            )
            return ActionResponse(
                action_id=action_id,
                action_type=action_type,
                status=ActionStatus.PENDING_CONFIRMATION,
                confirmation_required=True,
                confirmation_message=confirmation_msg,
                audit_id=audit_id
            )
        
        # Execute the action
        try:
            handler = getattr(self, f"_handle_{action_type.value}", None)
            if not handler:
                raise ValueError(f"No handler for action: {action_type.value}")
            
            result = await handler(user.tenant_id, parameters)
            
            audit_id = await self.log_audit(
                user.tenant_id, user.id, action_type, action_id,
                parameters, ActionStatus.EXECUTED, result=result
            )
            
            return ActionResponse(
                action_id=action_id,
                action_type=action_type,
                status=ActionStatus.EXECUTED,
                result=result,
                audit_id=audit_id
            )
            
        except Exception as e:
            audit_id = await self.log_audit(
                user.tenant_id, user.id, action_type, action_id,
                parameters, ActionStatus.FAILED, error=str(e)
            )
            return ActionResponse(
                action_id=action_id,
                action_type=action_type,
                status=ActionStatus.FAILED,
                error=str(e),
                audit_id=audit_id
            )
    
    def _get_confirmation_message(self, action_type: ActionType, params: Dict[str, Any]) -> str:
        """Generate confirmation message for destructive actions"""
        if action_type == ActionType.UPDATE_JOB_STATUS:
            job_name = params.get("job_name", "this job")
            new_status = params.get("status", "unknown")
            return f"Are you sure you want to change {job_name} status to '{new_status}'?"
        
        elif action_type == ActionType.UPDATE_MATERIAL_COST:
            material = params.get("material_name", "this material")
            new_cost = params.get("cost", 0)
            return f"Are you sure you want to update {material} cost to ${new_cost:.2f}? This will affect future quotes and jobs."
        
        elif action_type == ActionType.CREATE_INVOICE:
            customer = params.get("customer_name", "the customer")
            amount = params.get("total", 0)
            return f"Create invoice for {customer} totaling ${amount:.2f}?"
        
        elif action_type == ActionType.ASSIGN_EMPLOYEE:
            employee = params.get("employee_name", "the employee")
            job = params.get("job_name", "this job")
            return f"Assign {employee} to {job}?"
        
        return f"Confirm action: {action_type.value}?"
    
    # ============== ACTION HANDLERS ==============
    
    async def _handle_create_job(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job"""
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        job = {
            "id": job_id,
            "tenant_id": tenant_id,
            "name": params.get("name", "Untitled Job"),
            "description": params.get("description", ""),
            "customer_id": params.get("customer_id"),
            "customer_name": params.get("customer_name", ""),
            "category": params.get("category", "Other"),
            "status": "pending",
            "priority": params.get("priority", "normal"),
            "due_date": params.get("due_date"),
            "estimated_hours": params.get("estimated_hours"),
            "total": params.get("total", 0),
            "notes": params.get("notes", ""),
            "created_by": "ai_assistant",
            "created_at": now,
            "updated_at": now
        }
        
        await self.db.jobs.insert_one(job)
        
        return {
            "job_id": job_id,
            "name": job["name"],
            "status": job["status"],
            "message": f"Job '{job['name']}' created successfully"
        }

    async def _handle_create_order(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order in the current order workflow."""
        now = datetime.now(timezone.utc).isoformat()

        customer_id = params.get("customer_id")
        customer_name = (params.get("customer_name") or "").strip()
        company_name = (params.get("company_name") or "").strip()

        if not customer_id and customer_name:
            customer = await self.db.customers.find_one(
                {
                    "tenant_id": tenant_id,
                    "$or": [
                        {"name": {"$regex": f"^{customer_name}$", "$options": "i"}},
                        {"company": {"$regex": f"^{customer_name}$", "$options": "i"}},
                    ],
                },
                {"_id": 0, "id": 1, "name": 1, "company": 1},
            )
            if customer:
                customer_id = customer["id"]
                customer_name = customer.get("name") or customer_name
                company_name = company_name or customer.get("company") or ""

        if not customer_id and customer_name:
            customer_id = str(uuid.uuid4())
            customer_doc = {
                "id": customer_id,
                "tenant_id": tenant_id,
                "name": customer_name,
                "company": company_name or None,
                "phone": None,
                "email": None,
                "status": "lead",
                "notes": "Created by AI assistant",
                "profile_image_url": None,
                "is_tax_exempt": False,
                "tax_exempt_document_url": None,
                "portal_password_hash": None,
                "portal_enabled": False,
                "notification_preferences": {
                    "email_messages": True,
                    "email_orders": True,
                    "email_approvals": True,
                    "email_payments": True,
                },
                "created_at": now,
                "updated_at": now,
            }
            await self.db.customers.insert_one(customer_doc)

        last = await self.db.orders.find({"tenant_id": tenant_id}, {"_id": 0, "order_number": 1}).sort("date_created", -1).limit(1).to_list(1)
        order_number = f"ORD-{(await self.db.orders.count_documents({'tenant_id': tenant_id})) + 1:04d}"
        if last and last[0].get("order_number"):
            try:
                num = int(last[0]["order_number"].split("-")[-1])
                order_number = f"ORD-{num + 1:04d}"
            except (ValueError, IndexError):
                pass

        order_id = str(uuid.uuid4())
        order_doc = {
            "id": order_id,
            "order_number": order_number,
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "customer_name": customer_name or company_name or "New Customer",
            "company_name": company_name,
            "order_source": "ai_assistant",
            "date_created": params.get("date_created") or now[:10],
            "requested_due_date": params.get("requested_due_date"),
            "event_date": None,
            "status": "pending",
            "payment_status": "unpaid",
            "pickup_delivery_method": params.get("pickup_delivery_method") or "pickup",
            "pickup_delivery_notes": params.get("pickup_delivery_notes") or "",
            "internal_notes": params.get("description") or params.get("order_notes") or "Created by AI assistant",
            "created_by": "ai_assistant",
            "created_at": now,
            "updated_at": now,
            "is_archived": False,
            "job_tickets": [],
            "order_total": 0.0,
        }
        await self.db.orders.insert_one(order_doc)

        return {
            "order_id": order_id,
            "order_number": order_number,
            "customer_name": order_doc["customer_name"],
            "message": f"Order {order_number} created successfully for {order_doc['customer_name']}",
        }
    
    async def _handle_update_job_status(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update job status"""
        job_id = params.get("job_id")
        new_status = params.get("status")
        
        if not job_id or not new_status:
            raise ValueError("job_id and status are required")
        
        valid_statuses = ["pending", "in_progress", "production", "completed", "on_hold", "cancelled"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Verify job exists and belongs to tenant
        job = await self.db.jobs.find_one(
            {"id": job_id, "tenant_id": tenant_id},
            {"_id": 0, "name": 1, "status": 1}
        )
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        old_status = job.get("status")
        now = datetime.now(timezone.utc).isoformat()
        
        update_data = {
            "status": new_status,
            "updated_at": now
        }
        
        # Add completion timestamp if completing
        if new_status == "completed":
            update_data["completed_at"] = now
        
        await self.db.jobs.update_one(
            {"id": job_id, "tenant_id": tenant_id},
            {"$set": update_data}
        )
        
        return {
            "job_id": job_id,
            "job_name": job["name"],
            "old_status": old_status,
            "new_status": new_status,
            "message": f"Job '{job['name']}' status updated from '{old_status}' to '{new_status}'"
        }
    
    async def _handle_create_calendar_event(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event"""
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        event = {
            "id": event_id,
            "tenant_id": tenant_id,
            "title": params.get("title", "Untitled Event"),
            "description": params.get("description", ""),
            "start_time": params.get("start_time"),
            "end_time": params.get("end_time"),
            "all_day": params.get("all_day", False),
            "event_type": params.get("event_type", "general"),
            "location": params.get("location", ""),
            "attendees": params.get("attendees", []),
            "job_id": params.get("job_id"),
            "customer_id": params.get("customer_id"),
            "color": params.get("color", "#3B82F6"),
            "reminder": params.get("reminder", True),
            "created_by": "ai_assistant",
            "created_at": now,
            "updated_at": now
        }
        
        await self.db.calendar_events.insert_one(event)
        
        return {
            "event_id": event_id,
            "title": event["title"],
            "start_time": event["start_time"],
            "message": f"Calendar event '{event['title']}' created"
        }
    
    async def _handle_add_material(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new material to inventory"""
        material_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        material = {
            "id": material_id,
            "tenant_id": tenant_id,
            "name": params.get("name", "New Material"),
            "description": params.get("description", ""),
            "category": params.get("category", "General"),
            "sku": params.get("sku", f"MAT-{material_id[:8].upper()}"),
            "unit": params.get("unit", "each"),
            "cost": float(params.get("cost", 0)),
            "price": float(params.get("price", 0)),
            "quantity_in_stock": int(params.get("quantity", 0)),
            "reorder_level": int(params.get("reorder_level", 0)),
            "supplier": params.get("supplier", ""),
            "notes": params.get("notes", ""),
            "active": True,
            "created_by": "ai_assistant",
            "created_at": now,
            "updated_at": now
        }
        
        await self.db.materials.insert_one(material)
        
        return {
            "material_id": material_id,
            "name": material["name"],
            "sku": material["sku"],
            "cost": material["cost"],
            "message": f"Material '{material['name']}' added to inventory"
        }
    
    async def _handle_update_material_cost(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update material cost"""
        material_id = params.get("material_id")
        new_cost = float(params.get("cost", 0))
        
        if not material_id:
            raise ValueError("material_id is required")
        
        # Verify material exists and belongs to tenant
        material = await self.db.materials.find_one(
            {"id": material_id, "tenant_id": tenant_id},
            {"_id": 0, "name": 1, "cost": 1}
        )
        if not material:
            raise ValueError(f"Material not found: {material_id}")
        
        old_cost = material.get("cost", 0)
        now = datetime.now(timezone.utc).isoformat()
        
        await self.db.materials.update_one(
            {"id": material_id, "tenant_id": tenant_id},
            {"$set": {
                "cost": new_cost,
                "updated_at": now,
                "cost_updated_by": "ai_assistant"
            }}
        )
        
        # Log cost change history
        await self.db.material_cost_history.insert_one({
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "material_id": material_id,
            "old_cost": old_cost,
            "new_cost": new_cost,
            "changed_by": "ai_assistant",
            "created_at": now
        })
        
        return {
            "material_id": material_id,
            "name": material["name"],
            "old_cost": old_cost,
            "new_cost": new_cost,
            "message": f"Material '{material['name']}' cost updated from ${old_cost:.2f} to ${new_cost:.2f}"
        }
    
    async def _handle_create_invoice(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new invoice"""
        invoice_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Generate invoice number
        count = await self.db.invoices.count_documents({"tenant_id": tenant_id})
        invoice_number = f"INV-{count + 1:05d}"
        
        # Calculate totals
        line_items = params.get("line_items", [])
        subtotal = sum(item.get("total", 0) for item in line_items)
        tax_rate = float(params.get("tax_rate", 0))
        tax = subtotal * (tax_rate / 100)
        total = subtotal + tax
        
        invoice = {
            "id": invoice_id,
            "tenant_id": tenant_id,
            "invoice_number": invoice_number,
            "customer_id": params.get("customer_id"),
            "customer_name": params.get("customer_name", ""),
            "job_id": params.get("job_id"),
            "line_items": line_items,
            "subtotal": round(subtotal, 2),
            "tax_rate": tax_rate,
            "tax": round(tax, 2),
            "total": round(total, 2),
            "grand_total": round(total, 2),
            "status": "draft",
            "due_date": params.get("due_date"),
            "notes": params.get("notes", ""),
            "terms": params.get("terms", "Net 30"),
            "amount_paid": 0,
            "created_by": "ai_assistant",
            "created_at": now,
            "updated_at": now
        }
        
        await self.db.invoices.insert_one(invoice)
        
        return {
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "customer_name": invoice["customer_name"],
            "total": invoice["total"],
            "status": invoice["status"],
            "message": f"Invoice {invoice_number} created for ${invoice['total']:.2f}"
        }
    
    async def _handle_assign_employee(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Assign employee to a job"""
        job_id = params.get("job_id")
        employee_id = params.get("employee_id")
        
        if not job_id or not employee_id:
            raise ValueError("job_id and employee_id are required")
        
        # Verify job exists
        job = await self.db.jobs.find_one(
            {"id": job_id, "tenant_id": tenant_id},
            {"_id": 0, "name": 1, "assigned_employees": 1}
        )
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Verify employee exists
        employee = await self.db.employees.find_one(
            {"id": employee_id, "tenant_id": tenant_id},
            {"_id": 0, "name": 1}
        )
        if not employee:
            raise ValueError(f"Employee not found: {employee_id}")
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Add employee to job's assigned list
        current_assigned = job.get("assigned_employees", [])
        if employee_id not in current_assigned:
            current_assigned.append(employee_id)
        
        await self.db.jobs.update_one(
            {"id": job_id, "tenant_id": tenant_id},
            {"$set": {
                "assigned_employees": current_assigned,
                "updated_at": now
            }}
        )
        
        # Create assignment record
        assignment_id = str(uuid.uuid4())
        await self.db.job_assignments.insert_one({
            "id": assignment_id,
            "tenant_id": tenant_id,
            "job_id": job_id,
            "employee_id": employee_id,
            "assigned_by": "ai_assistant",
            "assigned_at": now
        })
        
        return {
            "assignment_id": assignment_id,
            "job_id": job_id,
            "job_name": job["name"],
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "message": f"{employee['name']} assigned to job '{job['name']}'"
        }
    
    async def _handle_log_time_entry(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log a time entry"""
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        hours = float(params.get("hours", 0))
        if hours <= 0:
            raise ValueError("Hours must be greater than 0")
        
        time_entry = {
            "id": entry_id,
            "tenant_id": tenant_id,
            "employee_id": params.get("employee_id"),
            "employee_name": params.get("employee_name", ""),
            "job_id": params.get("job_id"),
            "job_name": params.get("job_name", ""),
            "date": params.get("date", now[:10]),
            "hours": hours,
            "description": params.get("description", ""),
            "task_type": params.get("task_type", "general"),
            "billable": params.get("billable", True),
            "hourly_rate": float(params.get("hourly_rate", 0)),
            "status": "submitted",
            "created_by": "ai_assistant",
            "created_at": now
        }
        
        await self.db.time_entries.insert_one(time_entry)
        
        return {
            "entry_id": entry_id,
            "employee_name": time_entry["employee_name"],
            "job_name": time_entry["job_name"],
            "hours": time_entry["hours"],
            "date": time_entry["date"],
            "message": f"Time entry logged: {hours}h for {time_entry['employee_name'] or 'employee'}"
        }
    
    async def _handle_categorize_expense(self, tenant_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize or update expense category"""
        expense_id = params.get("expense_id")
        new_category = params.get("category")
        
        if not expense_id or not new_category:
            raise ValueError("expense_id and category are required")
        
        # Verify expense exists
        expense = await self.db.expenses.find_one(
            {"id": expense_id, "tenant_id": tenant_id},
            {"_id": 0, "description": 1, "category": 1, "amount": 1}
        )
        if not expense:
            raise ValueError(f"Expense not found: {expense_id}")
        
        old_category = expense.get("category", "Uncategorized")
        now = datetime.now(timezone.utc).isoformat()
        
        await self.db.expenses.update_one(
            {"id": expense_id, "tenant_id": tenant_id},
            {"$set": {
                "category": new_category,
                "updated_at": now,
                "categorized_by": "ai_assistant"
            }}
        )
        
        return {
            "expense_id": expense_id,
            "description": expense.get("description", ""),
            "amount": expense.get("amount", 0),
            "old_category": old_category,
            "new_category": new_category,
            "message": f"Expense categorized: '{old_category}' → '{new_category}'"
        }
    
    # ============== QUERY METHODS ==============
    
    async def get_action_audit_log(
        self,
        tenant_id: str,
        limit: int = 50,
        action_type: Optional[ActionType] = None
    ) -> List[Dict[str, Any]]:
        """Get audit log for AI actions"""
        query = {"tenant_id": tenant_id}
        if action_type:
            query["action_type"] = action_type.value
        
        entries = await self.db.ai_action_audit.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return entries
    
    async def get_pending_confirmations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get actions pending confirmation"""
        entries = await self.db.ai_action_audit.find(
            {
                "tenant_id": tenant_id,
                "status": ActionStatus.PENDING_CONFIRMATION.value
            },
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return entries


# ============== FACTORY FUNCTION ==============

def get_ai_assistant_actions(db) -> AIAssistantActions:
    """Get AIAssistantActions instance"""
    return AIAssistantActions(db)
