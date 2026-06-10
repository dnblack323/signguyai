"""
User, Authentication, and Tenant related Pydantic models.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from datetime import datetime, timezone
import uuid
from enum import Enum

from .enums import UserRole, TenantPlan


# ============== TENANT MODELS ==============
class TimeTrackingSettings(BaseModel):
    """Time tracking configuration for a tenant"""
    track_per_job: bool = True
    track_per_line_item: bool = False
    enable_employee_portal: bool = False
    enable_kiosk_mode: bool = False
    auto_suggest_on_status_change: bool = True


class PayrollSettings(BaseModel):
    """Payroll configuration for worksheet defaults and pay-week boundaries"""
    default_cycle: str = "weekly"
    pay_week_start_day: str = "monday"
    show_payroll_adjustments: bool = False


class BrandingSettings(BaseModel):
    """Tenant branding & template preferences applied to invoices, emails,
    and generated documents. All fields are optional so unconfigured tenants
    keep the existing default appearance (no regression)."""
    # ── Shared brand identity ──
    primary_color: str = "#0D9488"
    secondary_color: str = "#14B8A6"
    # ── Invoice layout & branding ──
    invoice_accent_color: Optional[str] = None        # falls back to primary_color
    invoice_show_logo: bool = True
    invoice_logo_position: str = "left"               # left | center | right
    invoice_show_company_info: bool = True
    invoice_footer_text: Optional[str] = None
    invoice_payment_terms: Optional[str] = None
    # ── Email branding ──
    email_from_name: Optional[str] = None             # overrides SendGrid from-name
    email_show_logo: bool = True
    email_header_color: Optional[str] = None          # falls back to primary_color
    email_signature: Optional[str] = None
    # ── Document branding ──
    document_show_logo: bool = True
    document_header_text: Optional[str] = None
    document_footer_text: Optional[str] = None


class TenantBase(BaseModel):
    name: str
    slug: str
    owner_email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "USA"
    website: Optional[str] = None
    logo_url: Optional[str] = None
    plan: TenantPlan = TenantPlan.STARTER  # Default to starter tier
    product_line: str = "os"  # os, webstores, or ai_studio
    is_active: bool = True
    is_founder: bool = False
    founder_number: Optional[int] = None
    founder_locked_at: Optional[str] = None
    time_tracking_settings: Optional[TimeTrackingSettings] = None
    payroll_settings: Optional[PayrollSettings] = None
    employee_portal_settings: Optional[Dict[str, bool]] = None
    signature_settings: Optional[Dict[str, Any]] = None
    branding_settings: Optional[BrandingSettings] = None
    default_tax_rate: Optional[float] = 0.0

class TenantCreate(BaseModel):
    name: str
    owner_email: EmailStr
    phone: Optional[str] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    time_tracking_settings: Optional[TimeTrackingSettings] = None
    payroll_settings: Optional[PayrollSettings] = None
    employee_portal_settings: Optional[Dict[str, bool]] = None
    customer_portal_settings: Optional[Dict[str, bool]] = None
    signature_settings: Optional[Dict[str, Any]] = None
    default_tax_rate: Optional[float] = None
    branding_settings: Optional[BrandingSettings] = None
    # AI Assistant personality — one of "ops_partner", "wise_mentor",
    # "cheerful_helper", "no_bs_direct". Defaults to ops_partner when unset.
    assistant_personality: Optional[str] = None
    # Set of action-types the tenant has opted out of confirmation for
    # (e.g. ["draft_email"]). Stored as a list; treated as a set.
    assistant_skip_confirm: Optional[List[str]] = None

class Tenant(TenantBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== USER MODELS ==============
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    company_name: Optional[str] = None
    is_active: bool = True
    role: UserRole = UserRole.STAFF
    tenant_id: Optional[str] = None
    is_founder: bool = False

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None
    role: Optional[UserRole] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UserInDB(User):
    hashed_password: str

class UserRoleUpdate(BaseModel):
    role: UserRole


# ============== TOKEN MODELS ==============
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None

class PasswordReset(BaseModel):
    new_password: str


# ============== PERMISSION DEFINITIONS ==============
class Permission(str, Enum):
    # Customer permissions
    CUSTOMERS_VIEW = "customers:view"
    CUSTOMERS_CREATE = "customers:create"
    CUSTOMERS_EDIT = "customers:edit"
    CUSTOMERS_DELETE = "customers:delete"
    
    # Quote permissions
    QUOTES_VIEW = "quotes:view"
    QUOTES_CREATE = "quotes:create"
    QUOTES_EDIT = "quotes:edit"
    QUOTES_DELETE = "quotes:delete"
    QUOTES_CONVERT = "quotes:convert"
    
    # Job permissions
    JOBS_VIEW = "jobs:view"
    JOBS_CREATE = "jobs:create"
    JOBS_EDIT = "jobs:edit"
    JOBS_DELETE = "jobs:delete"
    
    # Invoice permissions
    INVOICES_VIEW = "invoices:view"
    INVOICES_CREATE = "invoices:create"
    INVOICES_EDIT = "invoices:edit"
    INVOICES_DELETE = "invoices:delete"
    
    # Time Clock permissions
    TIME_CLOCK_OWN = "time:own"
    TIME_CLOCK_VIEW_ALL = "time:view_all"
    TIME_CLOCK_MANAGE = "time:manage"
    
    # Payroll permissions
    PAYROLL_VIEW = "payroll:view"
    PAYROLL_MANAGE = "payroll:manage"
    
    # Employee permissions
    EMPLOYEES_VIEW = "employees:view"
    EMPLOYEES_MANAGE = "employees:manage"
    
    # Financial permissions
    FINANCIALS_VIEW = "financials:view"
    FINANCIALS_MANAGE = "financials:manage"
    
    # User permissions
    USERS_VIEW = "users:view"
    USERS_MANAGE = "users:manage"
    
    # Settings permissions
    SETTINGS_VIEW = "settings:view"
    SETTINGS_MANAGE = "settings:manage"
    
    # Webstore permissions
    WEBSTORES_VIEW = "webstores:view"
    WEBSTORES_CREATE = "webstores:create"
    WEBSTORES_MANAGE = "webstores:manage"
    
    # Products permissions
    PRODUCTS_VIEW = "products:view"
    PRODUCTS_CREATE = "products:create"
    PRODUCTS_MANAGE = "products:manage"

    # Inventory and purchasing permissions
    INVENTORY_VIEW = "inventory:view"
    INVENTORY_PULL = "inventory:pull"
    INVENTORY_ADJUST = "inventory:adjust"
    PURCHASING_MANAGE = "purchasing:manage"
    PURCHASING_APPROVE = "purchasing:approve"
    VENDORS_MANAGE = "vendors:manage"

    # Platform Admin permissions
    PLATFORM_ADMIN_ACCESS = "platform_admin:access"
    PLATFORM_ADMIN_IMPERSONATE = "platform_admin:impersonate"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.PLATFORM_CREATOR: list(Permission),  # Platform creator (root) has all permissions
    UserRole.PLATFORM_ADMIN: list(Permission),  # Platform admins have all permissions including impersonation
    UserRole.OWNER: list(Permission),  # Owners have all permissions
    UserRole.ADMIN: [
        Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_CREATE, Permission.CUSTOMERS_EDIT, Permission.CUSTOMERS_DELETE,
        Permission.QUOTES_VIEW, Permission.QUOTES_CREATE, Permission.QUOTES_EDIT, Permission.QUOTES_DELETE, Permission.QUOTES_CONVERT,
        Permission.JOBS_VIEW, Permission.JOBS_CREATE, Permission.JOBS_EDIT, Permission.JOBS_DELETE,
        Permission.INVOICES_VIEW, Permission.INVOICES_CREATE, Permission.INVOICES_EDIT, Permission.INVOICES_DELETE,
        Permission.TIME_CLOCK_OWN, Permission.TIME_CLOCK_VIEW_ALL, Permission.TIME_CLOCK_MANAGE,
        Permission.PAYROLL_VIEW, Permission.PAYROLL_MANAGE,
        Permission.EMPLOYEES_VIEW, Permission.EMPLOYEES_MANAGE,
        Permission.FINANCIALS_VIEW,
        Permission.USERS_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.WEBSTORES_VIEW, Permission.WEBSTORES_CREATE, Permission.WEBSTORES_MANAGE,
        Permission.PRODUCTS_VIEW, Permission.PRODUCTS_CREATE, Permission.PRODUCTS_MANAGE,
        Permission.INVENTORY_VIEW, Permission.INVENTORY_PULL, Permission.INVENTORY_ADJUST,
        Permission.PURCHASING_MANAGE, Permission.VENDORS_MANAGE,
    ],
    UserRole.STAFF: [
        Permission.CUSTOMERS_VIEW, Permission.CUSTOMERS_CREATE, Permission.CUSTOMERS_EDIT,
        Permission.QUOTES_VIEW, Permission.QUOTES_CREATE, Permission.QUOTES_EDIT,
        Permission.JOBS_VIEW, Permission.JOBS_CREATE, Permission.JOBS_EDIT,
        Permission.INVOICES_VIEW,
        Permission.TIME_CLOCK_OWN,
        Permission.EMPLOYEES_VIEW,
        Permission.WEBSTORES_VIEW,
        Permission.PRODUCTS_VIEW,
        Permission.INVENTORY_VIEW, Permission.INVENTORY_PULL,
    ],
    # Webstore owners have NO tenant-side permissions — their access is gated
    # at the dedicated /api/owner-portal routes via a role check.
    UserRole.WEBSTORE_OWNER: [],
}


def get_user_permissions(role: UserRole) -> List[Permission]:
    """Get list of permissions for a given role"""
    return ROLE_PERMISSIONS.get(role, [])


def user_has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission"""
    return permission in ROLE_PERMISSIONS.get(role, [])
