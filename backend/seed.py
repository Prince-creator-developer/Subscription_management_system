from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models
from auth import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(models.User).filter(models.User.email == "admin@brightloop.com").first():
        print("Database already seeded.")
        db.close()
        return

    print("Seeding Brightloop Subscription Management System database...")

    # 1. Users & Staff
    admin = models.User(
        email="admin@brightloop.com",
        hashed_password=hash_password("Brightloop@2026!"),
        full_name="Prince Kumar (Admin)",
        role=models.UserRole.ADMIN.value,
        company_name="Brightloop Software HQ",
        phone="+91 9876543210"
    )
    staff = models.User(
        email="staff@brightloop.com",
        hashed_password=hash_password("Brightloop@2026!"),
        full_name="Yash Sharma (Billing Rep)",
        role=models.UserRole.STAFF.value,
        company_name="Brightloop Operations",
        phone="+91 9876543211"
    )
    customer1 = models.User(
        email="client@acmecorp.com",
        hashed_password=hash_password("Brightloop@2026!"),
        full_name="Sarah Jenkins",
        role=models.UserRole.CUSTOMER.value,
        company_name="Acme Corporation Ltd",
        phone="+91 9876543222"
    )
    customer2 = models.User(
        email="owner@nexustech.io",
        hashed_password=hash_password("Brightloop@2026!"),
        full_name="Vikram Mehta",
        role=models.UserRole.CUSTOMER.value,
        company_name="Nexus Tech Innovations",
        phone="+91 9876543233"
    )
    db.add_all([admin, staff, customer1, customer2])
    db.commit()

    # 2. Products & Variants (including +560 Odoo brand variant!)
    erp_product = models.Product(
        name="Brightloop ERP Core",
        product_type="software",
        sales_price=2499.0,
        cost_price=800.0,
        notes="Core enterprise resource planning and subscription engine"
    )
    analytics_addon = models.Product(
        name="Advanced AI Analytics Add-on",
        product_type="addon",
        sales_price=899.0,
        cost_price=200.0,
        notes="Real-time predictive forecasting and telemetry metrics"
    )
    support_service = models.Product(
        name="24/7 Priority Support SLA",
        product_type="service",
        sales_price=499.0,
        cost_price=100.0,
        notes="Dedicated account manager and 1-hour response SLA"
    )
    db.add_all([erp_product, analytics_addon, support_service])
    db.commit()

    # Variants: Odoo Brand adds 560 to price!
    odoo_variant = models.ProductVariant(
        product_id=erp_product.id,
        variant_name="Odoo Brand Edition",
        attribute_name="Brand",
        attribute_value="Odoo",
        price_extra=560.0
    )
    standard_variant = models.ProductVariant(
        product_id=erp_product.id,
        variant_name="Standard Open Edition",
        attribute_name="Brand",
        attribute_value="Standard",
        price_extra=0.0
    )
    db.add_all([odoo_variant, standard_variant])
    db.commit()

    # 3. Plans
    monthly_pro = models.Plan(
        name="Monthly Pro Suite",
        description="Billed every month with full access to modules and auto-renewal",
        cost=2999.0,
        billing_frequency=models.BillingFrequency.MONTHLY.value,
        min_quantity=1,
        auto_close=False,
        allow_early_close=True,
        allow_pause=True,
        allow_renew=True
    )
    yearly_ent = models.Plan(
        name="Yearly Enterprise Contract",
        description="Billed annually with dedicated infrastructure and SLA",
        cost=28990.0,
        billing_frequency=models.BillingFrequency.YEARLY.value,
        min_quantity=5,
        auto_close=False,
        allow_early_close=False,
        allow_pause=True,
        allow_renew=True
    )
    daily_sandbox = models.Plan(
        name="Daily Developer Sandbox",
        description="Ephemeral environment for testing integrations, auto-closes",
        cost=199.0,
        billing_frequency=models.BillingFrequency.DAILY.value,
        min_quantity=1,
        auto_close=True,
        allow_early_close=True,
        allow_pause=False,
        allow_renew=False
    )
    db.add_all([monthly_pro, yearly_ent, daily_sandbox])
    db.commit()

    # 4. Tax Rules
    gst18 = models.TaxRule(name="GST 18%", rate_percent=18.0, is_default=True)
    vat10 = models.TaxRule(name="VAT 10%", rate_percent=10.0, is_default=False)
    db.add_all([gst18, vat10])
    db.commit()

    # 5. Discount Rules
    discount_seats = models.DiscountRule(
        code="SEATS10",
        name="Volume Seat Discount 10%",
        discount_type=models.DiscountType.PERCENTAGE.value,
        value=10.0,
        min_purchase_amount=0.0,
        min_quantity=5,
        start_date=date.today() - timedelta(days=30),
        end_date=date.today() + timedelta(days=180),
        max_usage_limit=50,
        times_used=2
    )
    discount_flat = models.DiscountRule(
        code="SAVE500",
        name="Flat ₹500 Launch Incentive",
        discount_type=models.DiscountType.FIXED.value,
        value=500.0,
        min_purchase_amount=2000.0,
        min_quantity=1,
        start_date=date.today() - timedelta(days=15),
        end_date=date.today() + timedelta(days=60),
        max_usage_limit=100,
        times_used=8
    )
    db.add_all([discount_seats, discount_flat])
    db.commit()

    # 6. Quotation Template
    quote_template = models.QuotationTemplate(
        name="Enterprise SaaS Standard Onboarding",
        plan_id=monthly_pro.id,
        validity_days=15,
        notes="Standard quote template for mid-market clients"
    )
    db.add(quote_template)
    db.commit()

    qt_line1 = models.QuotationTemplateLine(
        template_id=quote_template.id,
        product_id=erp_product.id,
        variant_id=odoo_variant.id,
        quantity=1,
        unit_price=erp_product.sales_price + odoo_variant.price_extra
    )
    qt_line2 = models.QuotationTemplateLine(
        template_id=quote_template.id,
        product_id=analytics_addon.id,
        quantity=1,
        unit_price=analytics_addon.sales_price
    )
    db.add_all([qt_line1, qt_line2])
    db.commit()

    # 7. Subscriptions in various states
    # Sub 1: Active Subscription for Acme Corp
    sub1 = models.Subscription(
        subscription_number="SUB-2026-0001",
        customer_id=customer1.id,
        plan_id=monthly_pro.id,
        status=models.SubscriptionStatus.ACTIVE.value,
        start_date=date.today() - timedelta(days=45),
        expiry_date=date.today() + timedelta(days=320),
        next_billing_date=date.today(),  # Due today!
        payment_terms="Net 30",
        auto_close=False,
        notes="Acme Corporation primary billing contract"
    )
    db.add(sub1)
    db.commit()

    sub1_line1 = models.SubscriptionLine(
        subscription_id=sub1.id,
        product_id=erp_product.id,
        variant_id=odoo_variant.id,
        quantity=2,
        unit_price=3059.0,  # 2499 + 560
        tax_rate=18.0,
        discount_amount=0.0,
        subtotal=6118.0
    )
    sub1_line2 = models.SubscriptionLine(
        subscription_id=sub1.id,
        product_id=analytics_addon.id,
        quantity=1,
        unit_price=899.0,
        tax_rate=18.0,
        discount_amount=0.0,
        subtotal=899.0
    )
    db.add_all([sub1_line1, sub1_line2])
    db.commit()

    # Sub 2: Quotation state for Nexus Tech
    sub2 = models.Subscription(
        subscription_number="SUB-2026-0002",
        customer_id=customer2.id,
        plan_id=yearly_ent.id,
        status=models.SubscriptionStatus.QUOTATION.value,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        next_billing_date=date.today() + timedelta(days=30),
        payment_terms="Net 15",
        auto_close=False,
        notes="Pending quotation review by Nexus Tech procurement"
    )
    db.add(sub2)
    db.commit()

    sub2_line = models.SubscriptionLine(
        subscription_id=sub2.id,
        product_id=erp_product.id,
        variant_id=standard_variant.id,
        quantity=5,
        unit_price=2499.0,
        tax_rate=18.0,
        discount_amount=249.9,
        subtotal=12245.1
    )
    db.add(sub2_line)
    db.commit()

    # 8. Invoices: 1 Paid, 1 Confirmed (Overdue), 1 Draft
    inv1 = models.Invoice(
        invoice_number="INV-2026-0001",
        subscription_id=sub1.id,
        customer_id=customer1.id,
        status=models.InvoiceStatus.PAID.value,
        issue_date=date.today() - timedelta(days=35),
        due_date=date.today() - timedelta(days=5),
        subtotal=7017.0,
        tax_amount=1263.06,
        discount_amount=0.0,
        total_amount=8280.06,
        amount_paid=8280.06,
        balance_due=0.0,
        payment_terms="Net 30",
        notes="Billed for billing period Month 1"
    )
    db.add(inv1)
    db.commit()

    inv1_line = models.InvoiceLine(
        invoice_id=inv1.id,
        product_name="Brightloop ERP Core (Odoo Brand Edition)",
        variant_name="Odoo Edition (+₹560)",
        quantity=2,
        unit_price=3059.0,
        tax_rate=18.0,
        tax_amount=1101.24,
        discount_amount=0.0,
        total_amount=7219.24
    )
    db.add(inv1_line)
    db.commit()

    # Payment for inv1
    payment1 = models.Payment(
        payment_number="PAY-2026-0001",
        invoice_id=inv1.id,
        customer_id=customer1.id,
        amount=8280.06,
        payment_method=models.PaymentMethod.BANK_TRANSFER.value,
        payment_date=date.today() - timedelta(days=20),
        reference_id="HDFC-NEFT-99182371",
        note="Reconciled against invoice INV-2026-0001"
    )
    db.add(payment1)
    db.commit()

    # Inv2: Confirmed and Overdue!
    inv2 = models.Invoice(
        invoice_number="INV-2026-0002",
        subscription_id=sub1.id,
        customer_id=customer1.id,
        status=models.InvoiceStatus.CONFIRMED.value,
        issue_date=date.today() - timedelta(days=20),
        due_date=date.today() - timedelta(days=5),  # Past due date!
        subtotal=7017.0,
        tax_amount=1263.06,
        discount_amount=0.0,
        total_amount=8280.06,
        amount_paid=0.0,
        balance_due=8280.06,
        payment_terms="Net 15",
        notes="Awaiting bank transfer confirmation"
    )
    db.add(inv2)
    db.commit()

    print("Database seeding completed successfully.")
    db.close()

if __name__ == "__main__":
    seed_database()
