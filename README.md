# Brightloop Subscription Management System
> **Unified Recurring Billing, Plan Management & Revenue Intelligence Platform**  
> Developed for **Odoo x Make-A-Ton 9.0 Kochi Hackathon 2026**

---

## 🚀 Overview
Brightloop Software is an all-in-one subscription management and recurring billing platform engineered to automate the complete subscription lifecycle. It eliminates manual spreadsheets, missed renewals, double-invoicing, and scattered revenue tracking with an Odoo-inspired architecture.

### ✨ Key Capabilities
* **🔐 Multi-Role Access Control (RBAC):** Dedicated workflows for **Admin** (Catalog, Taxes, Discounts, Staff), **Internal Staff** (Sales Quotes, Subscriptions, Payments, Overdue tracking), and **Customer Portal** (Self-service subscriptions, invoices, receipts).
* **📦 Product & Variant Engine:** Support for software, add-ons, and brand variants with automatic price adjustments (e.g., Odoo Brand variant `+₹560`).
* **🔄 Flexible Subscription Lifecycle:** Pre-configured quotation templates moving through `Draft` → `Quotation` → `Confirmed` → `Active` → `Closed` (with Pause & Renew controls).
* **⚡ Idempotent Recurring Billing Engine:** Automated batch invoice generation from active subscriptions with zero duplicate billing or missed cycles.
* **🏷️ Dynamic Discount Rules:** Percentage and fixed discounts with minimum order thresholds, usage limits, and automatic expiration.
* **💳 Payment Ledger & A/R Aging:** Record payments across multiple methods, auto-reconcile invoices, and monitor overdue accounts in real-time.
* **📈 Executive Finance Intelligence:** Sub-200ms real-time dashboard delivering MRR, ARR, active subscriber churn, cash collections, and overdue aging breakdown.

---

## 👥 Team & Contribution Matrix
| Member | Role | Focus Areas |
| :--- | :--- | :--- |
| **Prince Kumar** | Team Leader & Backend Architect | FastAPI, SQLite/SQLAlchemy ORM, Billing Engine, Discount Engine, Invoicing & Analytics APIs |
| **Yash Sharma** | Frontend & UX Engineer | React (Vite), Tailwind CSS, Odoo-inspired UI, Customer Portal, Finance Dashboard, Input Validation |

---

## 🛠️ Architecture & Tech Stack
* **Frontend:** React 18, Vite, Tailwind CSS, Lucide React, Axios
* **Backend:** FastAPI (Python 3.11), Pydantic v2, SQLite (Local, offline-resilient), SQLAlchemy
* **Authentication:** Password validation with regex policies, JWT RBAC
* **Design Philosophy:** Clean, responsive, high-contrast Odoo-style modular design with intuitive spacing and toast notifications.

---

## ⚡ Quick Start Guide

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
Backend runs at `http://localhost:8000`  
Interactive Swagger API Docs: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

---

## 📜 Problem Statement Alignment
Built specifically to address all 7 business scenes from Brightloop Software's billing month challenge.
