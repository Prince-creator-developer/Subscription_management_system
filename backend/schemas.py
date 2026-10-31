from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
import re

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{9,}$")

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = "customer"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if len(v) <= 8:
            raise ValueError("Password must be more than 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.lower().strip()

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) <= 8:
            raise ValueError("Password must be more than 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("Password must contain at least one special character")
        return v

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Product & Variant Schemas
class ProductVariantCreate(BaseModel):
    variant_name: str
    attribute_name: str = "Brand"
    attribute_value: str = "Odoo"
    price_extra: float = 0.0

class ProductVariantResponse(BaseModel):
    id: int
    product_id: int
    variant_name: str
    attribute_name: str
    attribute_value: str
    price_extra: float
    is_active: bool

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    product_type: str = "software"
    sales_price: float
    cost_price: float = 0.0
    notes: Optional[str] = None
    variants: Optional[List[ProductVariantCreate]] = []

class ProductResponse(BaseModel):
    id: int
    name: str
    product_type: str
    sales_price: float
    cost_price: float
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    variants: List[ProductVariantResponse] = []

    class Config:
        from_attributes = True

# Plan Schemas
class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cost: float
    billing_frequency: str = "monthly"  # daily, weekly, monthly, yearly
    min_quantity: int = 1
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close: bool = False
    allow_early_close: bool = True
    allow_pause: bool = True
    allow_renew: bool = True

class PlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cost: float
    billing_frequency: str
    min_quantity: int
    available_from: Optional[date] = None
    available_to: Optional[date] = None
    auto_close: bool
    allow_early_close: bool
    allow_pause: bool
    allow_renew: bool
    is_active: bool

    class Config:
        from_attributes = True

# Tax Rule Schemas
class TaxRuleCreate(BaseModel):
    name: str
    rate_percent: float
    is_default: bool = False

class TaxRuleResponse(BaseModel):
    id: int
    name: str
    rate_percent: float
    is_default: bool
    is_active: bool

    class Config:
        from_attributes = True

# Discount Rule Schemas
class DiscountRuleCreate(BaseModel):
    code: str
    name: str
    discount_type: str = "percentage"
    value: float
    min_purchase_amount: float = 0.0
    min_quantity: int = 1
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_usage_limit: Optional[int] = None
    applicable_product_id: Optional[int] = None

class DiscountRuleResponse(BaseModel):
    id: int
    code: str
    name: str
    discount_type: str
    value: float
    min_purchase_amount: float
    min_quantity: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_usage_limit: Optional[int] = None
    times_used: int
    applicable_product_id: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True

# Subscription Line & Subscription Schemas
class SubscriptionLineCreate(BaseModel):
    product_id: int
    variant_id: Optional[int] = None
    quantity: int = 1
    unit_price: Optional[float] = None
    tax_rate: Optional[float] = 18.0
    discount_amount: Optional[float] = 0.0

class SubscriptionLineResponse(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    quantity: int
    unit_price: float
    tax_rate: float
    discount_amount: float
    subtotal: float
    product: Optional[ProductResponse] = None
    variant: Optional[ProductVariantResponse] = None

    class Config:
        from_attributes = True

class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int
    start_date: Optional[date] = None
    expiry_date: Optional[date] = None
    payment_terms: str = "Net 30"
    auto_close: bool = False
    applied_discount_code: Optional[str] = None
    notes: Optional[str] = None
    lines: List[SubscriptionLineCreate]

class SubscriptionResponse(BaseModel):
    id: int
    subscription_number: str
    customer_id: int
    plan_id: int
    status: str
    start_date: date
    expiry_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    payment_terms: str
    auto_close: bool
    notes: Optional[str] = None
    created_at: datetime
    customer: Optional[UserResponse] = None
    plan: Optional[PlanResponse] = None
    lines: List[SubscriptionLineResponse] = []

    class Config:
        from_attributes = True

# Invoice Line & Invoice Schemas
class InvoiceLineResponse(BaseModel):
    id: int
    product_name: str
    variant_name: Optional[str] = None
    quantity: int
    unit_price: float
    tax_rate: float
    tax_amount: float
    discount_amount: float
    total_amount: float

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    subscription_id: Optional[int] = None
    customer_id: int
    status: str
    issue_date: date
    due_date: date
    subtotal: float
    tax_amount: float
    discount_amount: float
    total_amount: float
    amount_paid: float
    balance_due: float
    payment_terms: str
    notes: Optional[str] = None
    created_at: datetime
    customer: Optional[UserResponse] = None
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True

# Payment Schemas
class PaymentCreate(BaseModel):
    invoice_id: int
    amount: float
    payment_method: str = "bank_transfer"
    payment_date: Optional[date] = None
    reference_id: Optional[str] = None
    note: Optional[str] = None

class PaymentResponse(BaseModel):
    id: int
    payment_number: str
    invoice_id: int
    customer_id: int
    amount: float
    payment_method: str
    payment_date: date
    reference_id: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Analytics Summary Schema
class FinanceAnalyticsSummary(BaseModel):
    active_subscriptions_count: int
    total_subscriptions_count: int
    mrr: float
    arr: float
    total_revenue_collected: float
    total_outstanding_ar: float
    overdue_invoices_count: int
    overdue_amount: float
    churn_rate_percent: float
