# ⚡ Brightloop Subscription Management Platform
> **Unified Recurring Billing, Plan Management & Revenue Intelligence Engine**  
> Developed for **Odoo x Make-A-Ton 9.0 Kochi Hackathon 2026**

---

## 🌐 Live Production Deployment
* **Live Web Application:** [https://subscriptionmanagementsystem-gamma.vercel.app/](https://subscriptionmanagementsystem-gamma.vercel.app/)
* **Vercel Multi-Service Architecture:** Configured via root `vercel.json` with reverse-proxy rewrites routing `/api/(.*)` to the Python backend and `/(.*)` to the Vite frontend.
* **Local Backend API:** `http://localhost:8000` (Interactive Swagger at `/docs`)
* **Local Frontend:** `http://localhost:5173`

---

## 👥 Team & Contribution Matrix
| Contributor | GitHub Account & Email | Core Ownership & Role |
| :--- | :--- | :--- |
| **Prince Kumar** (Team Leader) | `182784546+Prince-creator-developer@users.noreply.github.com` | Backend Architecture, SQLite ORM Models, RBAC Auth, Automated Billing Engine, Tax & Discount Engines, Test Suite |
| **Yash Sharma** | `yash28112005sharma@gmail.com` | Frontend Engineering, Odoo-styled UX, Interactive Quotation Builder, Customer Self-Service Portal, Admin Modals |

*Commits synchronized hourly across both team members in compliance with Odoo's version control evaluation criteria.*

---

## 🎯 Alignment with the 7 Brightloop Business Scenes

| # | Brightloop Business Scene | Technical Implementation |
| :---: | :--- | :--- |
| **1** | **Customer Signup & Strict Security** | Regex enforcement: `>8 chars`, 1 uppercase, 1 lowercase, 1 special symbol. Unique email validation, password reset tokens, and 3 distinct RBAC roles (`admin`, `staff`, `customer`). Admin-only staff provisioning. |
| **2** | **Product Variants & Multi-Frequency Plans** | Decoupled variant engine: choosing **Odoo Brand Edition** automatically applies a **+₹560** price uplift. Flexible billing recurrence (`Daily`, `Weekly`, `Monthly`, `Yearly`) with plan-by-plan controls for auto-closing, pausing, and renewals. |
| **3** | **Quotation Templates & State Machine** | Pre-configured quotation templates with validity windows. Full lifecycle state machine: `Draft` $\rightarrow$ `Quotation` $\rightarrow$ `Confirmed` $\rightarrow$ `Active` $\rightarrow$ `Closed` (with Pause/Resume). |
| **4** | **Automated Recurring Billing Day** | Batch automated billing (`POST /api/billing/run`) that scans active due subscriptions, generates itemized invoices, computes taxes (GST 18%), and enforces **idempotency safeguards** preventing double billing. |
| **5** | **Dynamic Discount Engine** | Admin-defined discount rules (percentage or fixed amount) with eligibility validation: minimum quantity, minimum spend threshold, validity dates, and usage limits. Automatically computed during quotation and invoice generation. |
| **6** | **Payment Collection & A/R Overdue Tracking** | Real-time payment ledger linking inward payments (Bank Transfer, Credit Card, UPI, Cheque, Cash) to invoices, instant balance reconciliation, and visual overdue aging alerts for proactive collection. |
| **7** | **Finance Lead Telemetry (< 2s Benchmark)** | High-speed aggregated metrics: Active Subscriptions, MRR, ARR, Cash Collections, Outstanding Accounts Receivable, and Overdue Aging. **Benchmark performance: ~14.11 ms** (exceeds the sub-2-second hackathon requirement by 140x). |

---

## 🧪 Automated Test Suite & Benchmark Results

The platform includes an automated unit and integration test suite (`backend/test_brightloop.py`):

```bash
cd backend
python test_brightloop.py
```

### Verified Test Results:
```text
......
----------------------------------------------------------------------
Ran 6 tests in 0.104s

OK

[BENCHMARK] Finance telemetry query latency: 14.11 ms (Target: < 2000 ms)
```

---

## 🔑 Evaluator Test Credentials & Personas

The application features a **one-click persona switcher** in the top navigation bar to evaluate each role without typing:

| Persona / Role | Email | Password | Primary Workflow to Test |
| :--- | :--- | :--- | :--- |
| **Admin (Prince Kumar)** | `admin@brightloop.com` | `Brightloop@2026!` | Full system control: Add Products & Variants (+₹560 rule), Create Billing Plans, Define Discount Rules, Run Billing Batch |
| **Staff (Yash Sharma)** | `staff@brightloop.com` | `Brightloop@2026!` | Sales & Operations: Create Quotations from Templates, Confirm Subscriptions, Record Inward Payments, Chase Overdue Invoices |
| **Customer (Sarah Jenkins - Acme Corp)** | `client@acmecorp.com` | `Brightloop@2026!` | Self-Service Portal: View active contracts, Pause/Renew subscriptions, View itemized invoices, Download payment receipts |

---

## 🛠️ Architecture & Tech Stack

```
Subscription_management_system/
├── backend/
│   ├── api/index.py              # Serverless entrypoint
│   ├── auth.py                   # PBKDF2 HMAC SHA-256 & JWT RBAC middleware
│   ├── database.py               # SQLite ORM engine (serverless /tmp resilient)
│   ├── main.py                   # FastAPI application & RESTful endpoints
│   ├── models.py                 # SQLAlchemy relational schemas
│   ├── requirements.txt          # Python runtime dependencies
│   ├── schemas.py                # Pydantic v2 schemas & regex password policy
│   ├── seed.py                   # Realistic Brightloop demonstration dataset
│   └── test_brightloop.py        # Automated test suite & latency benchmark
├── frontend/
│   ├── src/
│   │   ├── components/           # UI widgets & modals
│   │   ├── services/api.js       # Axios client with JWT interceptor
│   │   ├── App.jsx               # Master workspace (Odoo theme, tabs, modals)
│   │   ├── index.css             # Tailwind base & custom scrollbars
│   │   └── main.jsx              # Application bootstrap
│   ├── index.html                # Responsive viewport & branding
│   ├── package.json              # Node dependencies
│   ├── tailwind.config.js        # Official Odoo color palette configuration
│   └── vite.config.js            # Vite build & local proxy settings
├── vercel.json                   # Vercel multi-service orchestration
└── README.md                     # Comprehensive project documentation
```

---

## 🚀 Local Setup Instructions

### 1. Backend (Terminal 1)
```powershell
cd backend
pip install -r requirements.txt
python seed.py
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend (Terminal 2)
```powershell
cd frontend
npm install
npm run dev
```
Open [`http://localhost:5173`](http://localhost:5173) in your browser.
