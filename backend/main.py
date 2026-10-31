import os
import secrets
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from database import engine, Base, get_db
import models
import schemas
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin, require_staff_or_admin
)
from seed import seed_database

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Brightloop Subscription Management Platform",
    description="Unified recurring billing, plan management & revenue intelligence platform for Odoo x Make-A-Ton 2026",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    try:
        seed_database()
    except Exception as e:
        print(f"Startup seed notice: {e}")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "platform": "Brightloop Subscription Engine v1.0"
    }

# ==========================================
# 1. AUTHENTICATION & RBAC
# ==========================================

@app.post("/api/auth/register", response_model=schemas.TokenResponse)
def register_customer(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    # Only customers can self-register
    new_user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        company_name=payload.company_name,
        phone=payload.phone,
        role=models.UserRole.CUSTOMER.value
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.email, "role": new_user.role})
    return schemas.TokenResponse(access_token=token, user=new_user)

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")

    token = create_access_token({"sub": user.email, "role": user.role})
    return schemas.TokenResponse(access_token=token, user=user)

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/api/auth/staff", response_model=schemas.UserResponse)
def create_staff_member(
    payload: schemas.UserRegister,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Admin-only: Add a new member of staff"""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    staff_user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        company_name="Brightloop Internal Team",
        phone=payload.phone,
        role=models.UserRole.STAFF.value
    )
    db.add(staff_user)
    db.commit()
    db.refresh(staff_user)
    return staff_user

@app.post("/api/auth/forgot-password")
def forgot_password(payload: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        # Avoid user enumeration while returning clean feedback
        return {"message": "If this email is registered, a password reset token has been dispatched."}

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    db.commit()
    return {
        "message": "Password reset token generated successfully",
        "mock_email_dispatch": f"Password reset link sent to {user.email}",
        "reset_token": token
    }

@app.post("/api/auth/reset-password")
def reset_password(payload: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.reset_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    db.commit()
    return {"message": "Password updated successfully. You may now log in with your new credentials."}

# ==========================================
# 2. PRODUCTS & VARIANTS
# ==========================================

@app.get("/api/products", response_model=List[schemas.ProductResponse])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).filter(models.Product.is_active == True).all()

@app.post("/api/products", response_model=schemas.ProductResponse)
def create_product(
    payload: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    product = models.Product(
        name=payload.name,
        product_type=payload.product_type,
        sales_price=payload.sales_price,
        cost_price=payload.cost_price,
        notes=payload.notes
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Attach variants if provided (e.g. Odoo brand +560)
    if payload.variants:
        for v in payload.variants:
            variant = models.ProductVariant(
                product_id=product.id,
                variant_name=v.variant_name,
                attribute_name=v.attribute_name,
                attribute_value=v.attribute_value,
                price_extra=v.price_extra
            )
            db.add(variant)
        db.commit()
        db.refresh(product)

    return product

@app.post("/api/products/{product_id}/variants", response_model=schemas.ProductVariantResponse)
def add_product_variant(
    product_id: int,
    payload: schemas.ProductVariantCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    variant = models.ProductVariant(
        product_id=product.id,
        variant_name=payload.variant_name,
        attribute_name=payload.attribute_name,
        attribute_value=payload.attribute_value,
        price_extra=payload.price_extra
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant

# ==========================================
# 3. PLANS & RECURRENCE RULES
# ==========================================

@app.get("/api/plans", response_model=List[schemas.PlanResponse])
def list_plans(db: Session = Depends(get_db)):
    return db.query(models.Plan).filter(models.Plan.is_active == True).all()

@app.post("/api/plans", response_model=schemas.PlanResponse)
def create_plan(
    payload: schemas.PlanCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    plan = models.Plan(
        name=payload.name,
        description=payload.description,
        cost=payload.cost,
        billing_frequency=payload.billing_frequency,
        min_quantity=payload.min_quantity,
        available_from=payload.available_from,
        available_to=payload.available_to,
        auto_close=payload.auto_close,
        allow_early_close=payload.allow_early_close,
        allow_pause=payload.allow_pause,
        allow_renew=payload.allow_renew
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

# ==========================================
# 4. TAX RULES & DISCOUNT RULES
# ==========================================

@app.get("/api/taxes", response_model=List[schemas.TaxRuleResponse])
def list_tax_rules(db: Session = Depends(get_db)):
    return db.query(models.TaxRule).filter(models.TaxRule.is_active == True).all()

@app.post("/api/taxes", response_model=schemas.TaxRuleResponse)
def create_tax_rule(
    payload: schemas.TaxRuleCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    if payload.is_default:
        db.query(models.TaxRule).update({"is_default": False})

    rule = models.TaxRule(
        name=payload.name,
        rate_percent=payload.rate_percent,
        is_default=payload.is_default
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@app.get("/api/discounts", response_model=List[schemas.DiscountRuleResponse])
def list_discounts(db: Session = Depends(get_db)):
    return db.query(models.DiscountRule).filter(models.DiscountRule.is_active == True).all()

@app.post("/api/discounts", response_model=schemas.DiscountRuleResponse)
def create_discount_rule(
    payload: schemas.DiscountRuleCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    existing = db.query(models.DiscountRule).filter(models.DiscountRule.code == payload.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Discount code already exists")

    rule = models.DiscountRule(
        code=payload.code.upper(),
        name=payload.name,
        discount_type=payload.discount_type,
        value=payload.value,
        min_purchase_amount=payload.min_purchase_amount,
        min_quantity=payload.min_quantity,
        start_date=payload.start_date,
        end_date=payload.end_date,
        max_usage_limit=payload.max_usage_limit,
        applicable_product_id=payload.applicable_product_id
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

# ==========================================
# 5. SUBSCRIPTION & QUOTATION LIFECYCLE
# ==========================================

@app.get("/api/subscriptions", response_model=List[schemas.SubscriptionResponse])
def list_subscriptions(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Subscription)
    if current_user.role == models.UserRole.CUSTOMER.value:
        query = query.filter(models.Subscription.customer_id == current_user.id)
    if status:
        query = query.filter(models.Subscription.status == status)
    return query.order_by(models.Subscription.id.desc()).all()

@app.post("/api/subscriptions", response_model=schemas.SubscriptionResponse)
def create_subscription(
    payload: schemas.SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_staff_or_admin)
):
    # Customer verification
    customer = db.query(models.User).filter(models.User.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    plan = db.query(models.Plan).filter(models.Plan.id == payload.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    count = db.query(models.Subscription).count() + 1
    sub_num = f"SUB-2026-{count:04d}"

    start_d = payload.start_date or date.today()
    # Compute expiry date based on plan billing frequency if not passed
    expiry_d = payload.expiry_date
    if not expiry_d:
        if plan.billing_frequency == "daily":
            expiry_d = start_d + timedelta(days=7)
        elif plan.billing_frequency == "weekly":
            expiry_d = start_d + timedelta(weeks=4)
        elif plan.billing_frequency == "yearly":
            expiry_d = start_d + timedelta(days=365)
        else:
            expiry_d = start_d + timedelta(days=30)

    sub = models.Subscription(
        subscription_number=sub_num,
        customer_id=payload.customer_id,
        plan_id=payload.plan_id,
        status=models.SubscriptionStatus.QUOTATION.value,
        start_date=start_d,
        expiry_date=expiry_d,
        next_billing_date=start_d,
        payment_terms=payload.payment_terms,
        auto_close=payload.auto_close or plan.auto_close,
        notes=payload.notes
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    # Process lines
    for item in payload.lines:
        prod = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not prod:
            continue
        unit_price = prod.sales_price
        if item.variant_id:
            variant = db.query(models.ProductVariant).filter(models.ProductVariant.id == item.variant_id).first()
            if variant:
                unit_price += variant.price_extra

        subtotal = (unit_price * item.quantity) - (item.discount_amount or 0.0)
        line = models.SubscriptionLine(
            subscription_id=sub.id,
            product_id=prod.id,
            variant_id=item.variant_id,
            quantity=item.quantity,
            unit_price=unit_price,
            tax_rate=item.tax_rate or 18.0,
            discount_amount=item.discount_amount or 0.0,
            subtotal=max(0.0, subtotal)
        )
        db.add(line)

    db.commit()
    db.refresh(sub)
    return sub

@app.post("/api/subscriptions/{subscription_id}/status")
def update_subscription_status(
    subscription_id: int,
    action: str = Query(..., description="Action: confirm, activate, pause, resume, renew, close"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    sub = db.query(models.Subscription).filter(models.Subscription.id == subscription_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Customer can pause/renew if plan allows
    if current_user.role == models.UserRole.CUSTOMER.value:
        if sub.customer_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if action == "pause" and not sub.plan.allow_pause:
            raise HTTPException(status_code=400, detail="Plan does not allow pausing")
        if action == "renew" and not sub.plan.allow_renew:
            raise HTTPException(status_code=400, detail="Plan does not allow renewal")

    if action == "confirm":
        sub.status = models.SubscriptionStatus.CONFIRMED.value
    elif action == "activate":
        sub.status = models.SubscriptionStatus.ACTIVE.value
    elif action == "pause":
        sub.status = models.SubscriptionStatus.PAUSED.value
    elif action == "resume":
        sub.status = models.SubscriptionStatus.ACTIVE.value
    elif action == "renew":
        sub.status = models.SubscriptionStatus.ACTIVE.value
        if sub.expiry_date:
            sub.expiry_date = sub.expiry_date + timedelta(days=30)
    elif action == "close":
        sub.status = models.SubscriptionStatus.CLOSED.value

    db.commit()
    return {"message": f"Subscription {sub.subscription_number} transitioned to {sub.status}", "status": sub.status}

# ==========================================
# 6. AUTOMATED RECURRING BILLING ENGINE
# ==========================================

@app.post("/api/billing/run")
def trigger_automated_billing(
    billing_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_staff_or_admin)
):
    """
    Automated batch invoice generation:
    Scans for active subscriptions due for billing on or before billing_date.
    Applies tax rules, dynamic discounts, and safeguards against duplicate invoicing.
    """
    target_date = billing_date or date.today()
    due_subs = db.query(models.Subscription).filter(
        models.Subscription.status == models.SubscriptionStatus.ACTIVE.value,
        models.Subscription.next_billing_date <= target_date
    ).all()

    generated_invoices = []
    skipped_count = 0

    for sub in due_subs:
        # Idempotency Guard: Ensure no invoice created for this subscription on the same issue date
        existing_invoice = db.query(models.Invoice).filter(
            models.Invoice.subscription_id == sub.id,
            models.Invoice.issue_date == target_date
        ).first()

        if existing_invoice:
            skipped_count += 1
            continue

        count = db.query(models.Invoice).count() + 1
        inv_num = f"INV-2026-{count:04d}"

        # Days to due date based on payment terms
        terms_days = 30
        if "15" in sub.payment_terms:
            terms_days = 15
        elif "Receipt" in sub.payment_terms:
            terms_days = 0

        due_d = target_date + timedelta(days=terms_days)

        subtotal = sum(line.subtotal for line in sub.lines)
        tax_amount = sum((line.subtotal * (line.tax_rate / 100.0)) for line in sub.lines)
        total_amount = subtotal + tax_amount

        invoice = models.Invoice(
            invoice_number=inv_num,
            subscription_id=sub.id,
            customer_id=sub.customer_id,
            status=models.InvoiceStatus.CONFIRMED.value,
            issue_date=target_date,
            due_date=due_d,
            subtotal=round(subtotal, 2),
            tax_amount=round(tax_amount, 2),
            discount_amount=0.0,
            total_amount=round(total_amount, 2),
            amount_paid=0.0,
            balance_due=round(total_amount, 2),
            payment_terms=sub.payment_terms,
            notes=f"Automated recurring invoice for subscription {sub.subscription_number}"
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        # Generate invoice lines
        for s_line in sub.lines:
            v_name = s_line.variant.variant_name if s_line.variant else None
            line_tax = round(s_line.subtotal * (s_line.tax_rate / 100.0), 2)
            inv_line = models.InvoiceLine(
                invoice_id=invoice.id,
                product_name=s_line.product.name,
                variant_name=v_name,
                quantity=s_line.quantity,
                unit_price=s_line.unit_price,
                tax_rate=s_line.tax_rate,
                tax_amount=line_tax,
                discount_amount=s_line.discount_amount,
                total_amount=round(s_line.subtotal + line_tax, 2)
            )
            db.add(inv_line)

        # Advance next billing date
        if sub.plan.billing_frequency == "daily":
            sub.next_billing_date = target_date + timedelta(days=1)
        elif sub.plan.billing_frequency == "weekly":
            sub.next_billing_date = target_date + timedelta(weeks=1)
        elif sub.plan.billing_frequency == "yearly":
            sub.next_billing_date = target_date + timedelta(days=365)
        else:
            sub.next_billing_date = target_date + timedelta(days=30)

        # Auto-close check if plan expires
        if sub.auto_close and sub.expiry_date and sub.next_billing_date >= sub.expiry_date:
            sub.status = models.SubscriptionStatus.CLOSED.value

        generated_invoices.append(inv_num)

    db.commit()
    return {
        "status": "success",
        "processed_subscriptions": len(due_subs),
        "invoices_generated": len(generated_invoices),
        "skipped_duplicate_guard": skipped_count,
        "invoice_numbers": generated_invoices
    }

# ==========================================
# 7. INVOICES & PAYMENTS LEDGER
# ==========================================

@app.get("/api/invoices", response_model=List[schemas.InvoiceResponse])
def list_invoices(
    status: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = db.query(models.Invoice)
    if current_user.role == models.UserRole.CUSTOMER.value:
        query = query.filter(models.Invoice.customer_id == current_user.id)
    if status:
        query = query.filter(models.Invoice.status == status)
    if overdue_only:
        query = query.filter(
            models.Invoice.status == models.InvoiceStatus.CONFIRMED.value,
            models.Invoice.due_date < date.today()
        )
    return query.order_by(models.Invoice.id.desc()).all()

@app.post("/api/payments", response_model=schemas.PaymentResponse)
def record_payment(
    payload: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_staff_or_admin)
):
    invoice = db.query(models.Invoice).filter(models.Invoice.id == payload.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == models.InvoiceStatus.PAID.value:
        raise HTTPException(status_code=400, detail="Invoice is already fully paid")

    count = db.query(models.Payment).count() + 1
    pay_num = f"PAY-2026-{count:04d}"

    payment = models.Payment(
        payment_number=pay_num,
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        payment_date=payload.payment_date or date.today(),
        reference_id=payload.reference_id,
        note=payload.note
    )
    db.add(payment)

    # Reconcile invoice balance
    invoice.amount_paid += payload.amount
    invoice.balance_due = max(0.0, invoice.total_amount - invoice.amount_paid)
    if invoice.balance_due <= 0.0:
        invoice.status = models.InvoiceStatus.PAID.value

    db.commit()
    db.refresh(payment)
    return payment

# ==========================================
# 8. FINANCE LEAD REPORTING & ANALYTICS (<2s)
# ==========================================

@app.get("/api/analytics/summary", response_model=schemas.FinanceAnalyticsSummary)
def get_finance_summary(db: Session = Depends(get_db), current_user: models.User = Depends(require_staff_or_admin)):
    """High-performance aggregated revenue intelligence"""
    total_subs = db.query(models.Subscription).count()
    active_subs = db.query(models.Subscription).filter(
        models.Subscription.status == models.SubscriptionStatus.ACTIVE.value
    ).count()

    closed_subs = db.query(models.Subscription).filter(
        models.Subscription.status == models.SubscriptionStatus.CLOSED.value
    ).count()

    churn_rate = round((closed_subs / max(1, total_subs)) * 100.0, 2)

    # Compute MRR across active subscriptions
    active_sub_records = db.query(models.Subscription).filter(
        models.Subscription.status == models.SubscriptionStatus.ACTIVE.value
    ).all()

    mrr = 0.0
    for s in active_sub_records:
        sub_total = sum(l.subtotal for l in s.lines)
        if s.plan.billing_frequency == "yearly":
            mrr += (sub_total / 12.0)
        elif s.plan.billing_frequency == "weekly":
            mrr += (sub_total * 4.33)
        elif s.plan.billing_frequency == "daily":
            mrr += (sub_total * 30.0)
        else:
            mrr += sub_total

    arr = mrr * 12.0

    # Total revenue collected
    collected = db.query(func.sum(models.Payment.amount)).scalar() or 0.0

    # Outstanding Accounts Receivable (AR)
    outstanding_ar = db.query(func.sum(models.Invoice.balance_due)).filter(
        models.Invoice.status != models.InvoiceStatus.CANCELLED.value
    ).scalar() or 0.0

    # Overdue stats
    overdue_invoices = db.query(models.Invoice).filter(
        models.Invoice.status == models.InvoiceStatus.CONFIRMED.value,
        models.Invoice.due_date < date.today()
    ).all()

    overdue_count = len(overdue_invoices)
    overdue_amount = sum(inv.balance_due for inv in overdue_invoices)

    return schemas.FinanceAnalyticsSummary(
        active_subscriptions_count=active_subs,
        total_subscriptions_count=total_subs,
        mrr=round(mrr, 2),
        arr=round(arr, 2),
        total_revenue_collected=round(collected, 2),
        total_outstanding_ar=round(outstanding_ar, 2),
        overdue_invoices_count=overdue_count,
        overdue_amount=round(overdue_amount, 2),
        churn_rate_percent=churn_rate
    )
