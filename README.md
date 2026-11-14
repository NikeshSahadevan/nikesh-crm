# 🚀 Nikesh CRM — Full-Stack Sales Pipeline & Lead Management System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://nikesh-crm.streamlit.app/)

🔗 **Live Application:** [https://nikesh-crm.streamlit.app/](https://nikesh-crm.streamlit.app/)


A role-based, full-stack Customer Relationship Management (CRM) web application built with **Python**, **Streamlit**, and **PostgreSQL**. Designed for sales teams to track leads, manage follow-up schedules, analyze pipeline conversion metrics, and export formatted Excel reports.

---

## ✨ Key Features

- **🔐 Authentication & Role-Based Access Control (RBAC):**
  - Secure login with SHA-256 password hashing.
  - **Admin Role:** Full system control, user account creation, granular feature permission toggles (`Add`, `Edit`, `Delete`, `Export`, `Analytics`), and direct user password resets.
  - **Staff User Role:** Dynamic UI rendering based on permissions assigned by the Admin, plus self-service password updates.
- **📊 Sales Pipeline & Follow-up Tracking:**
  - Full CRUD operations backed by PostgreSQL (`New`, `Lead`, `Contacted`, `Qualified`, `Won`, `Lost`).
  - Real-time KPI cards (Total Pipeline, Active Leads, Won Deals, Due/Overdue Follow-ups).
  - Case-insensitive search across lead names and call notes, plus stage-based filtering.
- **📈 Pipeline Analytics:**
  - Interactive stage distribution bar chart and automated win-rate calculation.
- **📥 Formatted Excel (`.xlsx`) Export:**
  - Exports leads into styled Excel workbooks using `openpyxl` with text-formatted phone numbers and auto-fitted column widths.
- **🖥️ 1-Click Desktop Launcher:**
  - Includes Windows `.bat` script configuration for instant local startup without opening an IDE.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit, Custom CSS
- **Backend:** Python (Modular 3-tier architecture: `app.py`, `crm.py`, `storage.py`)
- **Database:** PostgreSQL (`psycopg2`)
- **Reporting & Security:** `openpyxl`, `python-dotenv`, `hashlib` (SHA-256)

---

## ⚙️ Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/NikeshSahadevan/nikesh-crm.git](https://github.com/NikeshSahadevan/nikesh-crm.git)
   cd nikesh-crm

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL Database:**
   Create a database named `mini_crm` and run the following SQL schema:
   ```sql
   CREATE TABLE leads (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       number VARCHAR(20) NOT NULL,
       status VARCHAR(50) DEFAULT 'Lead',
       follow_up_date DATE,
       notes TEXT DEFAULT '',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```
   *(Note: The `users` table and default Admin account are initialized automatically on first launch.)*

4. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and update your PostgreSQL and Admin login credentials:
   ```bash
   cp .env.example .env
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```