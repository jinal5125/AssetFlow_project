# AssetFlow – IT Asset Management System

AssetFlow is a modern, enterprise-ready IT Asset Lifecycle Management web application built with **Django** and **Python**. It provides IT administrators and organizations with full visibility into their hardware inventory, asset allocations to employees, maintenance logs, QR code generation & scanning, and real-time analytical reporting with CSV exports.

---

## 🚀 Key Features

* **📊 Executive Dashboard**: High-level overview of total assets, available hardware, active assignments, maintenance requests, and recent returns with interactive doughnut charts.
* **💻 Asset Inventory (CRUD)**: Manage enterprise hardware (laptops, monitors, workstations, peripherals) tracking brand, purchase price, purchase date, asset codes, and lifecycle status (`Available`, `Assigned`, `Maintenance`, `Retired`).
* **👥 Employee Directory (CRUD)**: Maintain employee records including department, email, phone, and joining date to ensure complete accountability.
* **🔄 Assignment & Return Workflow**: Deploy available assets to staff members with assignment dates and remarks. Return assets back to inventory with a single click, instantly updating status.
* **🛠️ Maintenance & Repair Tracking**: Log hardware incidents, schedule repairs, track repair costs, and transition tickets through `Open`, `In Progress`, and `Completed` statuses.
* **📱 QR Code Generation & Mobile Scanning**:
  * Automatically generates unique QR codes for every asset.
  * Encodes direct URLs that resolve seamlessly across local networks (LAN) for smartphone camera scanning.
  * Directs anyone scanning an asset sticker to a public Asset Details page displaying specifications, active assignment, and maintenance history.
  * Features a graceful **"Asset Not Found"** page if an invalid code is scanned.
  * Includes a built-in Quick QR Lookup / Scan modal on the web interface.
* **📈 Reports & Analytics Module**:
  * Real-time metrics computed directly from database records.
  * Interactive **Chart.js** visualizations for Asset Status Distribution and Category breakdowns.
  * Multi-criteria filtering by **Asset Status**, **Category**, and **Purchase Date Range**.
  * Filtered data tables for inventory, employee allocations, and maintenance history.
* **⬇️ One-Click CSV Export**:
  * Integrated directly into the Reports module.
  * Exports Assets (with active filter support), Assignments, and Maintenance logs in standard CSV format.
* **🔐 Dual-Layer Authentication**:
  * **AssetFlow User Panel** (`/`): Registration and login for application users.
  * **Django Administration Panel** (`/admin/`): Dedicated interface for system superusers.

---

## 🛠️ Technologies Used

* **Backend**: Python 3.10+, Django 5.x / 6.x
* **Database**: SQLite3 (default development database, easily configurable for PostgreSQL / MySQL)
* **Frontend**: Vanilla HTML5, CSS3, JavaScript (Inter Typography, Modern Responsive Design)
* **Visualizations**: [Chart.js](https://www.chartjs.org/) (via CDN)
* **QR Code Engine**: `qrcode`, `Pillow`
* **Exporting**: Python standard `csv` library

---

## 📁 Project Structure

```text
assetflow/
├── assetflow/                  # Django project configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py             # App settings, ALLOWED_HOSTS, installed apps
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py
├── assets/                     # Core application module
│   ├── migrations/             # Database migrations
│   ├── templates/assets/       # Application HTML templates
│   │   ├── add_asset.html
│   │   ├── add_assignment.html
│   │   ├── add_employee.html
│   │   ├── add_maintenance.html
│   │   ├── asset_detail.html   # QR scan landing page (public view)
│   │   ├── asset_qr.html       # Asset QR code view & label printing
│   │   ├── assets_list.html    # Inventory table with QR lookup modal
│   │   ├── assignments_list.html
│   │   ├── dashboard.html      # Main dashboard & status chart
│   │   ├── delete_asset.html
│   │   ├── delete_employee.html
│   │   ├── edit_asset.html
│   │   ├── edit_employee.html
│   │   ├── edit_maintenance.html
│   │   ├── employees_list.html
│   │   ├── login.html          # AssetFlow login page
│   │   ├── maintenance_list.html
│   │   ├── register.html       # AssetFlow registration page
│   │   ├── reports.html        # Comprehensive reports & analytics
│   │   └── return_asset.html
│   ├── admin.py                # Django admin registrations
│   ├── apps.py
│   ├── models.py               # Employee, Category, Asset, Assignment, Maintenance
│   ├── urls.py                 # Application routes
│   └── views.py                # Controller views & business logic
├── db.sqlite3                  # SQLite database
├── manage.py                   # Django CLI management script
└── README.md
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
Ensure you have **Python 3.10+** and `pip` installed on your machine.

### 2. Clone the Repository
```bash
git clone <repository-url>
cd assetflow
```

### 3. Create & Activate a Virtual Environment
* **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
* **Windows (Command Prompt)**:
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```
* **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 4. Install Dependencies
Install all required packages:
```bash
pip install django qrcode pillow
```

### 5. Apply Database Migrations
Run Django migrations to configure the SQLite database schema:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Admin Access)
Create an administrator account for accessing the Django Admin panel at `/admin/`:
```bash
python manage.py createsuperuser
```
Follow the interactive prompt to set your admin username, email, and password.

---

## 🚀 Running the Project

### Local Development
To run the server on your local machine:
```bash
python manage.py runserver
```
Open your browser and navigate to:
* **AssetFlow Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Mobile / Local Network Access (for QR Code Scanning)
To scan QR codes from your smartphone camera or another device on the same Wi-Fi network, start the server bound to `0.0.0.0`:
```bash
python manage.py runserver 0.0.0.0:8000
```
AssetFlow will automatically detect your local network IP (e.g. `192.168.1.5:8000`) and encode it into generated QR codes, allowing mobile devices to scan stickers directly.

---

## 📖 Module Overviews

### 1. Dashboard (`/`)
* Displays summary cards for Total Assets, Available Hardware, Active Allocations, and Items under Maintenance.
* Includes an interactive Chart.js doughnut chart depicting current hardware status distribution.
* Highlights recent asset return events.

### 2. Assets Management (`/assets/`)
* Comprehensive asset inventory with search filtering by asset name, unique code, or manufacturer.
* Dropdown filters for Category and Lifecycle Status.
* Action buttons for Edit, Delete, QR Code generation, and Direct Details inspection.
* Built-in **"📷 Scan / Lookup QR"** modal allowing instant asset lookup by code or scanned URL.

### 3. Employee Directory (`/employees/`)
* Manage organization personnel records with department tags, email, and phone contact details.

### 4. Assignments & Lifecycle (`/assignments/`)
* Assign inventory items to designated employees. Assets transition to `Assigned` status automatically.
* One-click return workflow marks hardware returned and releases it back to `Available` inventory.

### 5. Maintenance Tickets (`/maintenance/`)
* Track hardware defects, battery replacements, or repair jobs.
* Completing a maintenance ticket automatically restores the asset status to `Available`.

### 6. QR Code Workflow (`/assets/qr/<id>/` & `/assets/detail/<id>/`)
* Generates high-resolution QR codes encoding the asset's detail URL.
* Scanning the QR code opens the clean **Asset Details Page** (`/assets/detail/<id>/`), displaying:
  * Asset Name, ID, Category, Serial / Asset Code, Brand, Purchase Date, and Price.
  * Active allocation info (Employee name, department, email, phone, assignment date).
  * Complete maintenance history log (Issue, reported date, repair date, cost, status).
* Does not require authentication for scanning so physical equipment can be inspected on the warehouse/office floor.
* Displays a user-friendly **"Asset Not Found"** notification if an invalid or removed asset ID is queried.

### 7. Reports & Analytics (`/reports/`)
* Complete real-time management reporting based strictly on database records (no mock data).
* Top-level asset valuation and allocation status statistics.
* Interactive Doughnut chart (Status Breakdown) and Bar chart (Assets per Category).
* Multi-parameter filter form (Status, Category, Date From, Date To).
* Filtered inventory summary tables, employee allocation tables, and maintenance expenditures.

### 8. CSV Export (`/export/...`)
* Connected directly to the Reports section:
  * `export_assets_csv`: Exports all or filtered assets matching current report criteria.
  * `export_assignments_csv`: Exports employee assignment history.
  * `export_maintenance_csv`: Exports repair logs and maintenance expenditures.

---

## 🔧 Important Configuration Notes

### Network Settings (`ALLOWED_HOSTS`)
In `assetflow/settings.py`, `ALLOWED_HOSTS = ['*']` is enabled for local development to ensure smartphones and testing devices on your Wi-Fi network can scan and access the application without `DisallowedHost` errors. For production deployment, specify your exact domain names.

### Static & Media Files
Static assets (CSS, fonts, Chart.js) are organized via standard Django static handling:
```python
STATIC_URL = 'static/'
```

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
