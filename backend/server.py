from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, date, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Sign Guy AI API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== ENUMS ==============
class CustomerStatus(str, Enum):
    LEAD = "lead"
    ACTIVE = "active"
    INACTIVE = "inactive"

class QuoteStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    DECLINED = "declined"

class JobStatus(str, Enum):
    QUOTED = "quoted"
    APPROVED = "approved"
    IN_PRODUCTION = "in_production"
    INSTALLED = "installed"
    COMPLETE = "complete"

class JobItemStatus(str, Enum):
    PENDING = "pending"
    IN_PRODUCTION = "in_production"
    DONE = "done"

class JobItemType(str, Enum):
    BANNER = "banner"
    YARD_SIGN = "yard_sign"
    DECAL = "decal"
    WRAP = "wrap"
    INSTALL = "install"
    DESIGN = "design"
    VEHICLE_GRAPHICS = "vehicle_graphics"
    WINDOW_GRAPHICS = "window_graphics"
    DIMENSIONAL_LETTERS = "dimensional_letters"
    MONUMENT_SIGN = "monument_sign"
    OTHER = "other"

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"

class PayrollTransactionType(str, Enum):
    EARNINGS = "earnings"
    ADVANCE = "advance"
    PAYMENT = "payment"

class ExpenseCategory(str, Enum):
    MATERIALS = "materials"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    UTILITIES = "utilities"
    RENT = "rent"
    OTHER = "other"

# ============== MODELS ==============

# Customer Models
class CustomerBase(BaseModel):
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: CustomerStatus = CustomerStatus.LEAD
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[CustomerStatus] = None
    notes: Optional[str] = None

class Customer(CustomerBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Quote Models
class QuoteLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float
    total: float = 0

class QuoteBase(BaseModel):
    customer_id: str
    line_items: List[QuoteLineItem] = []
    notes: Optional[str] = None
    status: QuoteStatus = QuoteStatus.DRAFT

class QuoteCreate(QuoteBase):
    pass

class QuoteUpdate(BaseModel):
    line_items: Optional[List[QuoteLineItem]] = None
    notes: Optional[str] = None
    status: Optional[QuoteStatus] = None

class Quote(QuoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total: float = 0
    job_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Job Models
class JobBase(BaseModel):
    customer_id: str
    name: str
    description: Optional[str] = None
    status: JobStatus = JobStatus.QUOTED
    due_date: Optional[str] = None

class JobCreate(JobBase):
    quote_id: Optional[str] = None

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[JobStatus] = None
    due_date: Optional[str] = None

class Job(JobBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quote_id: Optional[str] = None
    invoice_id: Optional[str] = None
    subtotal: float = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# JobItem Models (Line Items for Jobs)
class JobItemBase(BaseModel):
    job_id: str
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    unit_price: float = 0
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None

class JobItemCreate(JobItemBase):
    pass

class JobItemUpdate(BaseModel):
    item_type: Optional[JobItemType] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    status: Optional[JobItemStatus] = None
    notes: Optional[str] = None

class JobItem(JobItemBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    line_total: float = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Invoice Models
class InvoiceBase(BaseModel):
    customer_id: str
    job_id: Optional[str] = None
    total: float = 0
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: Optional[str] = None
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    total: Optional[float] = None
    status: Optional[InvoiceStatus] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None

class Invoice(InvoiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    paid_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Employee Models
class EmployeeBase(BaseModel):
    name: str
    hourly_rate: float
    is_active: bool = True

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    is_active: Optional[bool] = None

class Employee(EmployeeBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Time Clock Models
class TimeLogBase(BaseModel):
    employee_id: str
    action: str  # start_work, break_start, break_end, end_work
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TimeLogCreate(BaseModel):
    employee_id: str
    action: str

class TimeLog(TimeLogBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class DailyShiftSummary(BaseModel):
    employee_id: str
    date: str
    work_minutes: float = 0
    break_minutes: float = 0
    net_minutes: float = 0

# Payroll Models
class PayrollTransactionBase(BaseModel):
    employee_id: str
    type: PayrollTransactionType
    amount: float
    description: Optional[str] = None
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())

class PayrollTransactionCreate(PayrollTransactionBase):
    pass

class PayrollTransaction(PayrollTransactionBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PayrollBalance(BaseModel):
    employee_id: str
    employee_name: str
    total_earnings: float = 0
    total_advances: float = 0
    total_payments: float = 0
    balance: float = 0  # Positive = employer owes employee

# Financial Models
class SalesEntryBase(BaseModel):
    date: str
    amount: float
    tax_amount: float = 0
    description: Optional[str] = None

class SalesEntryCreate(SalesEntryBase):
    pass

class SalesEntry(SalesEntryBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ExpenseEntryBase(BaseModel):
    date: str
    amount: float
    category: ExpenseCategory = ExpenseCategory.OTHER
    description: Optional[str] = None

class ExpenseEntryCreate(ExpenseEntryBase):
    pass

class ExpenseEntry(ExpenseEntryBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FinancialSummary(BaseModel):
    total_sales: float = 0
    total_tax: float = 0
    total_expenses: float = 0
    net_income: float = 0

# Task Models
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    job_id: Optional[str] = None
    due_date: Optional[str] = None
    is_complete: bool = False

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    job_id: Optional[str] = None
    due_date: Optional[str] = None
    is_complete: Optional[bool] = None

class Task(TaskBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# AI Request Models
class AIRequest(BaseModel):
    tool: str
    input_data: Dict[str, Any]

class AIResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool: str
    input_data: Dict[str, Any]
    output: str
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Webstore Models
class FundraiserCampaign(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    goal: float
    start_date: str
    end_date: str
    organizer: str
    payout_rules: Optional[str] = None
    products: List[str] = []
    total_raised: float = 0
    status: str = "active"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class FundraiserCampaignCreate(BaseModel):
    name: str
    goal: float
    start_date: str
    end_date: str
    organizer: str
    payout_rules: Optional[str] = None
    products: List[str] = []

class B2BStore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    contact_email: str
    login_password: str
    allowed_products: List[str] = []
    discount_percent: float = 0
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class B2BStoreCreate(BaseModel):
    company_name: str
    contact_email: str
    login_password: str
    allowed_products: List[str] = []
    discount_percent: float = 0

class WebstoreOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_type: str  # fundraiser or b2b
    store_id: str
    items: List[Dict[str, Any]] = []
    total: float = 0
    status: str = "pending"
    job_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WebstoreOrderCreate(BaseModel):
    store_type: str
    store_id: str
    items: List[Dict[str, Any]]
    total: float

# ============== ROUTES ==============

# Root
@api_router.get("/")
async def root():
    return {"message": "Sign Guy AI API", "version": "1.0.0"}

# Health Check
@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# -------------- CUSTOMERS --------------
@api_router.post("/customers", response_model=Customer)
async def create_customer(input: CustomerCreate):
    customer = Customer(**input.model_dump())
    doc = customer.model_dump()
    await db.customers.insert_one(doc)
    return customer

@api_router.get("/customers", response_model=List[Customer])
async def get_customers(
    status: Optional[CustomerStatus] = None,
    search: Optional[str] = None
):
    query = {}
    if status:
        query["status"] = status.value
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    return customers

@api_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@api_router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(customer_id: str, input: CustomerUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.customers.update_one({"id": customer_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return customer

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    result = await db.customers.delete_one({"id": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}

# -------------- QUOTES --------------
@api_router.post("/quotes", response_model=Quote)
async def create_quote(input: QuoteCreate):
    # Calculate totals for line items
    line_items = []
    total = 0
    for item in input.line_items:
        item_total = item.quantity * item.unit_price
        line_items.append(QuoteLineItem(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item_total
        ))
        total += item_total
    
    quote = Quote(
        customer_id=input.customer_id,
        line_items=line_items,
        notes=input.notes,
        status=input.status,
        total=total
    )
    doc = quote.model_dump()
    await db.quotes.insert_one(doc)
    return quote

@api_router.get("/quotes", response_model=List[Quote])
async def get_quotes(
    customer_id: Optional[str] = None,
    status: Optional[QuoteStatus] = None
):
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    quotes = await db.quotes.find(query, {"_id": 0}).to_list(1000)
    return quotes

@api_router.get("/quotes/{quote_id}", response_model=Quote)
async def get_quote(quote_id: str):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@api_router.put("/quotes/{quote_id}", response_model=Quote)
async def update_quote(quote_id: str, input: QuoteUpdate):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Cannot update quote that has been converted to job")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Recalculate total if line items changed
    if "line_items" in update_data:
        total = 0
        processed_items = []
        for item in update_data["line_items"]:
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else item
            item_total = item_dict["quantity"] * item_dict["unit_price"]
            item_dict["total"] = item_total
            processed_items.append(item_dict)
            total += item_total
        update_data["line_items"] = processed_items
        update_data["total"] = total
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    updated_quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    return updated_quote

@api_router.post("/quotes/{quote_id}/convert-to-job", response_model=Job)
async def convert_quote_to_job(quote_id: str):
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Quote already converted to job")
    
    # Create job from quote
    job = Job(
        customer_id=quote["customer_id"],
        name=f"Job from Quote #{quote_id[:8]}",
        description=quote.get("notes", ""),
        status=JobStatus.APPROVED,
        quote_id=quote_id
    )
    job_doc = job.model_dump()
    await db.jobs.insert_one(job_doc)
    
    # Update quote with job_id
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"job_id": job.id, "status": QuoteStatus.APPROVED.value}}
    )
    
    return job

# -------------- JOBS --------------
@api_router.post("/jobs", response_model=Job)
async def create_job(input: JobCreate):
    job = Job(**input.model_dump())
    doc = job.model_dump()
    await db.jobs.insert_one(doc)
    return job

@api_router.get("/jobs", response_model=List[Job])
async def get_jobs(
    customer_id: Optional[str] = None,
    status: Optional[JobStatus] = None
):
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    jobs = await db.jobs.find(query, {"_id": 0}).to_list(1000)
    return jobs

@api_router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.put("/jobs/{job_id}", response_model=Job)
async def update_job(job_id: str, input: JobUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.jobs.update_one({"id": job_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    return job

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    result = await db.jobs.delete_one({"id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted"}

# -------------- INVOICES --------------
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(input: InvoiceCreate):
    invoice = Invoice(**input.model_dump())
    doc = invoice.model_dump()
    await db.invoices.insert_one(doc)
    
    # Link invoice to job if job_id provided
    if input.job_id:
        await db.jobs.update_one({"id": input.job_id}, {"$set": {"invoice_id": invoice.id}})
    
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(
    customer_id: Optional[str] = None,
    status: Optional[InvoiceStatus] = None
):
    query = {}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, input: InvoiceUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # If marking as paid, set paid_date
    if input.status == InvoiceStatus.PAID:
        update_data["paid_date"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.invoices.update_one({"id": invoice_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    return invoice

@api_router.post("/invoices/from-job/{job_id}", response_model=Invoice)
async def create_invoice_from_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get quote total if quote exists
    total = 0
    if job.get("quote_id"):
        quote = await db.quotes.find_one({"id": job["quote_id"]}, {"_id": 0})
        if quote:
            total = quote.get("total", 0)
    
    invoice = Invoice(
        customer_id=job["customer_id"],
        job_id=job_id,
        total=total,
        status=InvoiceStatus.DRAFT
    )
    doc = invoice.model_dump()
    await db.invoices.insert_one(doc)
    
    # Update job with invoice_id
    await db.jobs.update_one({"id": job_id}, {"$set": {"invoice_id": invoice.id}})
    
    return invoice

# -------------- EMPLOYEES --------------
@api_router.post("/employees", response_model=Employee)
async def create_employee(input: EmployeeCreate):
    employee = Employee(**input.model_dump())
    doc = employee.model_dump()
    await db.employees.insert_one(doc)
    return employee

@api_router.get("/employees", response_model=List[Employee])
async def get_employees(is_active: Optional[bool] = None):
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    return employees

@api_router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@api_router.put("/employees/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, input: EmployeeUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    result = await db.employees.update_one({"id": employee_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    return employee

# -------------- TIME CLOCK --------------
@api_router.post("/timeclock", response_model=TimeLog)
async def clock_action(input: TimeLogCreate):
    valid_actions = ["start_work", "break_start", "break_end", "end_work"]
    if input.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    # Get today's logs for this employee
    today = datetime.now(timezone.utc).date().isoformat()
    today_logs = await db.timelogs.find({
        "employee_id": input.employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    
    # Validate sequence
    last_action = today_logs[-1]["action"] if today_logs else None
    
    valid_sequences = {
        None: ["start_work"],
        "start_work": ["break_start", "end_work"],
        "break_start": ["break_end"],
        "break_end": ["break_start", "end_work"],
        "end_work": ["start_work"]
    }
    
    if input.action not in valid_sequences.get(last_action, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid sequence. After '{last_action}', valid actions are: {valid_sequences.get(last_action, [])}"
        )
    
    time_log = TimeLog(
        employee_id=input.employee_id,
        action=input.action,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    doc = time_log.model_dump()
    await db.timelogs.insert_one(doc)
    return time_log

@api_router.get("/timeclock/{employee_id}/today")
async def get_today_logs(employee_id: str):
    today = datetime.now(timezone.utc).date().isoformat()
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return logs

@api_router.get("/timeclock/{employee_id}/summary")
async def get_shift_summary(employee_id: str, date: Optional[str] = None):
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()
    
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{date}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    
    work_minutes = 0
    break_minutes = 0
    work_start = None
    break_start = None
    
    for log in logs:
        ts = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
        action = log["action"]
        
        if action == "start_work":
            work_start = ts
        elif action == "break_start" and work_start:
            break_start = ts
        elif action == "break_end" and break_start:
            break_minutes += (ts - break_start).total_seconds() / 60
            break_start = None
        elif action == "end_work" and work_start:
            work_minutes += (ts - work_start).total_seconds() / 60
            work_start = None
    
    return {
        "employee_id": employee_id,
        "date": date,
        "work_minutes": round(work_minutes, 2),
        "break_minutes": round(break_minutes, 2),
        "net_minutes": round(work_minutes - break_minutes, 2),
        "net_hours": round((work_minutes - break_minutes) / 60, 2)
    }

@api_router.get("/timeclock/{employee_id}/status")
async def get_clock_status(employee_id: str):
    today = datetime.now(timezone.utc).date().isoformat()
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", -1).to_list(1)
    
    if not logs:
        return {"status": "not_started", "last_action": None}
    
    last_log = logs[0]
    status_map = {
        "start_work": "working",
        "break_start": "on_break",
        "break_end": "working",
        "end_work": "finished"
    }
    
    return {
        "status": status_map.get(last_log["action"], "unknown"),
        "last_action": last_log["action"],
        "last_timestamp": last_log["timestamp"]
    }

# -------------- PAYROLL --------------
@api_router.post("/payroll/transactions", response_model=PayrollTransaction)
async def create_payroll_transaction(input: PayrollTransactionCreate):
    transaction = PayrollTransaction(**input.model_dump())
    doc = transaction.model_dump()
    await db.payroll_transactions.insert_one(doc)
    return transaction

@api_router.get("/payroll/transactions", response_model=List[PayrollTransaction])
async def get_payroll_transactions(
    employee_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    query = {}
    if employee_id:
        query["employee_id"] = employee_id
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    transactions = await db.payroll_transactions.find(query, {"_id": 0}).to_list(1000)
    return transactions

@api_router.get("/payroll/balance/{employee_id}", response_model=PayrollBalance)
async def get_payroll_balance(employee_id: str):
    employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    transactions = await db.payroll_transactions.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
    
    total_earnings = sum(t["amount"] for t in transactions if t["type"] == "earnings")
    total_advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
    total_payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
    
    # Balance = Earnings - Advances - Payments
    # Positive = employer owes employee
    # Negative = employee overpaid (has advance)
    balance = total_earnings - total_advances - total_payments
    
    return PayrollBalance(
        employee_id=employee_id,
        employee_name=employee["name"],
        total_earnings=total_earnings,
        total_advances=total_advances,
        total_payments=total_payments,
        balance=balance
    )

@api_router.get("/payroll/report")
async def get_payroll_report(start_date: str, end_date: str):
    employees = await db.employees.find({}, {"_id": 0}).to_list(1000)
    report = []
    
    for emp in employees:
        transactions = await db.payroll_transactions.find({
            "employee_id": emp["id"],
            "date": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}).to_list(1000)
        
        earnings = sum(t["amount"] for t in transactions if t["type"] == "earnings")
        advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
        payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
        
        report.append({
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "period_earnings": earnings,
            "period_advances": advances,
            "period_payments": payments,
            "period_balance": earnings - advances - payments
        })
    
    return report

# -------------- FINANCIALS --------------
@api_router.post("/financials/sales", response_model=SalesEntry)
async def create_sales_entry(input: SalesEntryCreate):
    entry = SalesEntry(**input.model_dump())
    doc = entry.model_dump()
    await db.sales_entries.insert_one(doc)
    return entry

@api_router.get("/financials/sales", response_model=List[SalesEntry])
async def get_sales_entries(start_date: Optional[str] = None, end_date: Optional[str] = None):
    query = {}
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    entries = await db.sales_entries.find(query, {"_id": 0}).to_list(1000)
    return entries

@api_router.post("/financials/expenses", response_model=ExpenseEntry)
async def create_expense_entry(input: ExpenseEntryCreate):
    entry = ExpenseEntry(**input.model_dump())
    doc = entry.model_dump()
    await db.expense_entries.insert_one(doc)
    return entry

@api_router.get("/financials/expenses", response_model=List[ExpenseEntry])
async def get_expense_entries(
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None,
    category: Optional[ExpenseCategory] = None
):
    query = {}
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    if category:
        query["category"] = category.value
    
    entries = await db.expense_entries.find(query, {"_id": 0}).to_list(1000)
    return entries

@api_router.get("/financials/summary", response_model=FinancialSummary)
async def get_financial_summary(start_date: str, end_date: str):
    sales = await db.sales_entries.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(1000)
    
    expenses = await db.expense_entries.find({
        "date": {"$gte": start_date, "$lte": end_date}
    }, {"_id": 0}).to_list(1000)
    
    total_sales = sum(s["amount"] for s in sales)
    total_tax = sum(s.get("tax_amount", 0) for s in sales)
    total_expenses = sum(e["amount"] for e in expenses)
    
    return FinancialSummary(
        total_sales=total_sales,
        total_tax=total_tax,
        total_expenses=total_expenses,
        net_income=total_sales - total_expenses
    )

# -------------- TASKS --------------
@api_router.post("/tasks", response_model=Task)
async def create_task(input: TaskCreate):
    task = Task(**input.model_dump())
    doc = task.model_dump()
    await db.tasks.insert_one(doc)
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(job_id: Optional[str] = None, is_complete: Optional[bool] = None):
    query = {}
    if job_id:
        query["job_id"] = job_id
    if is_complete is not None:
        query["is_complete"] = is_complete
    tasks = await db.tasks.find(query, {"_id": 0}).to_list(1000)
    return tasks

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, input: TaskUpdate):
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    result = await db.tasks.update_one({"id": task_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return task

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}

# -------------- AI TOOLS --------------
@api_router.post("/ai/generate", response_model=AIResponse)
async def generate_ai_content(request: AIRequest):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Build prompt based on tool type
    tool_prompts = {
        "layout_generator": """You are a sign design layout expert. Create multiple layout concepts based on the input.
Input: {input}
Provide:
1. 3 different layout concepts with text hierarchy, spacing guidance, and design rationale
2. Color recommendations based on provided colors
3. Font pairing suggestions
4. Key design principles for this type of sign""",
        
        "print_checklist": """You are a print production expert. Review this design for print-readiness.
Input: {input}
Check and report on:
1. Bleed margins (recommended 0.125" or 3mm)
2. Color contrast and accessibility
3. Text sizing and hierarchy
4. Image resolution requirements
5. File format recommendations
Provide a checklist with pass/fail status for each item.""",
        
        "brand_kit": """You are a branding expert. Create a brand kit based on this input.
Input: {input}
Generate:
1. Color palette (primary, secondary, accent colors with hex codes)
2. Font pairings (heading and body fonts)
3. 5 tagline options
4. Brand voice guidelines
5. Logo usage recommendations""",
        
        "document_creator": """You are a business document specialist for sign shops.
Input: {input}
Create a professional {document_type} document including all relevant sections.""",
        
        "overdue_assistant": """You are a collections specialist for sign shops. Analyze this overdue invoice.
Input: {input}
Provide:
1. A professional reminder message (email format)
2. Suggested follow-up actions
3. Timeline recommendations""",
        
        "design_intake": """You are a design intake specialist for sign shops. Based on this conversation:
Input: {input}
Extract and structure:
1. Product type
2. Dimensions
3. Text content
4. Color preferences
5. Logo requirements
6. Special requests
7. Deadline
Format as a structured job ticket."""
    }
    
    prompt_template = tool_prompts.get(request.tool)
    if not prompt_template:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {request.tool}")
    
    prompt = prompt_template.format(input=str(request.input_data), **request.input_data)
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=str(uuid.uuid4()),
            system_message="You are a helpful AI assistant for Sign Guy AI, a sign shop management system."
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Save AI response
        ai_response = AIResponse(
            tool=request.tool,
            input_data=request.input_data,
            output=response,
            job_id=request.input_data.get("job_id"),
            customer_id=request.input_data.get("customer_id")
        )
        doc = ai_response.model_dump()
        await db.ai_responses.insert_one(doc)
        
        return ai_response
    except Exception as e:
        logger.error(f"AI generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

@api_router.get("/ai/history", response_model=List[AIResponse])
async def get_ai_history(
    tool: Optional[str] = None,
    job_id: Optional[str] = None,
    customer_id: Optional[str] = None
):
    query = {}
    if tool:
        query["tool"] = tool
    if job_id:
        query["job_id"] = job_id
    if customer_id:
        query["customer_id"] = customer_id
    
    responses = await db.ai_responses.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return responses

# -------------- WEBSTORES: FUNDRAISER --------------
@api_router.post("/webstores/fundraiser", response_model=FundraiserCampaign)
async def create_fundraiser(input: FundraiserCampaignCreate):
    campaign = FundraiserCampaign(**input.model_dump())
    doc = campaign.model_dump()
    await db.fundraiser_campaigns.insert_one(doc)
    return campaign

@api_router.get("/webstores/fundraiser", response_model=List[FundraiserCampaign])
async def get_fundraisers(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    campaigns = await db.fundraiser_campaigns.find(query, {"_id": 0}).to_list(100)
    return campaigns

@api_router.get("/webstores/fundraiser/{campaign_id}", response_model=FundraiserCampaign)
async def get_fundraiser(campaign_id: str):
    campaign = await db.fundraiser_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@api_router.put("/webstores/fundraiser/{campaign_id}")
async def update_fundraiser(campaign_id: str, update_data: Dict[str, Any]):
    result = await db.fundraiser_campaigns.update_one({"id": campaign_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign = await db.fundraiser_campaigns.find_one({"id": campaign_id}, {"_id": 0})
    return campaign

# -------------- WEBSTORES: B2B --------------
@api_router.post("/webstores/b2b", response_model=B2BStore)
async def create_b2b_store(input: B2BStoreCreate):
    store = B2BStore(**input.model_dump())
    doc = store.model_dump()
    await db.b2b_stores.insert_one(doc)
    return store

@api_router.get("/webstores/b2b", response_model=List[B2BStore])
async def get_b2b_stores(is_active: Optional[bool] = None):
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    stores = await db.b2b_stores.find(query, {"_id": 0}).to_list(100)
    return stores

@api_router.get("/webstores/b2b/{store_id}", response_model=B2BStore)
async def get_b2b_store(store_id: str):
    store = await db.b2b_stores.find_one({"id": store_id}, {"_id": 0})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store

@api_router.post("/webstores/b2b/{store_id}/login")
async def b2b_store_login(store_id: str, password: str = Query(...)):
    store = await db.b2b_stores.find_one({"id": store_id}, {"_id": 0})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    if store["login_password"] != password:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"message": "Login successful", "store_id": store_id}

# -------------- WEBSTORE ORDERS --------------
@api_router.post("/webstores/orders", response_model=WebstoreOrder)
async def create_webstore_order(input: WebstoreOrderCreate):
    order = WebstoreOrder(**input.model_dump())
    
    # Auto-create job from order
    customer_name = f"Webstore {input.store_type.upper()} Customer"
    
    # Create or find customer
    existing_customer = await db.customers.find_one({"company": customer_name}, {"_id": 0})
    if not existing_customer:
        customer = Customer(name=customer_name, company=customer_name, status=CustomerStatus.ACTIVE)
        await db.customers.insert_one(customer.model_dump())
        customer_id = customer.id
    else:
        customer_id = existing_customer["id"]
    
    # Create job
    job = Job(
        customer_id=customer_id,
        name=f"Webstore Order #{order.id[:8]}",
        description=f"Order from {input.store_type} store {input.store_id}",
        status=JobStatus.APPROVED
    )
    await db.jobs.insert_one(job.model_dump())
    
    order.job_id = job.id
    doc = order.model_dump()
    await db.webstore_orders.insert_one(doc)
    
    # Update fundraiser total if applicable
    if input.store_type == "fundraiser":
        await db.fundraiser_campaigns.update_one(
            {"id": input.store_id},
            {"$inc": {"total_raised": input.total}}
        )
    
    return order

@api_router.get("/webstores/orders", response_model=List[WebstoreOrder])
async def get_webstore_orders(
    store_type: Optional[str] = None,
    store_id: Optional[str] = None
):
    query = {}
    if store_type:
        query["store_type"] = store_type
    if store_id:
        query["store_id"] = store_id
    orders = await db.webstore_orders.find(query, {"_id": 0}).to_list(1000)
    return orders

# -------------- DASHBOARD STATS --------------
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Count totals
    total_customers = await db.customers.count_documents({})
    active_jobs = await db.jobs.count_documents({"status": {"$nin": ["complete"]}})
    pending_invoices = await db.invoices.count_documents({"status": {"$in": ["sent", "overdue"]}})
    
    # Get today's sales
    today_sales = await db.sales_entries.find({"date": today}, {"_id": 0}).to_list(100)
    today_revenue = sum(s["amount"] for s in today_sales)
    
    # Get overdue invoices
    overdue_invoices = await db.invoices.find({"status": "overdue"}, {"_id": 0}).to_list(100)
    overdue_total = sum(i["total"] for i in overdue_invoices)
    
    return {
        "total_customers": total_customers,
        "active_jobs": active_jobs,
        "pending_invoices": pending_invoices,
        "today_revenue": today_revenue,
        "overdue_total": overdue_total,
        "overdue_count": len(overdue_invoices)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
