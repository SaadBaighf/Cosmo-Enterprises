
# Cosmo Enterprises-DBMS Project)

## Overview

The Chemical Company Management System is a Django-based web application designed to manage the internal operations of a chemical company. The system provides centralized control over clients, vendors, inventory, orders, payments, and invoice generation, enabling efficient tracking of business transactions and resources.

This project was developed as part of the Database Management System (DBMS) and follows a modular, database-driven architecture.

# Features

## Dashboards 

- Home Dashboard
- Client Dashboard
- Order Dashboard
- Inventory Dashboard
- Finance Dashboard
- Reorder Dashboard

## Authentication  

- Secure admin login system
- Restricted access to internal dashboards

## Client Management

- Create, update and manage client records
- Store contact details and profile images

## Vendor Management

- Maintain supplier(vendor) information
- Associate vendors with supplied materials

## Inventory & Material Management

- Add and manage raw materials
- Track stock quantity and pricing
- Inventory updates based on transactions

## Order Management

- Create client orders
- Assign materials and quantities
- Automatic calculation of total orders

## Payment & Finance Tracking

- Record payments against orders
- Track paid and remaining balances
- Financial overview via dashboard

## Invoice Generation

- Generate proffesional invoices per order
- Export invoices as PDF using WeasyPrint




## Technology Stack

**Backend:** Python, Django

**Frontend:** Bootstrap, JavaScript

**Database:** SQLite (development)

**PDF Export:** WeasyPrint

**Environment:** Python Virtual Environment
# Installation & Setup

## Prerequisites

- Python 3.9 or later
- pip (Python package manager)
- Virtual environment support

## Steps

### 1. Clone the repository

```bash
git clone <repository-url>
cd Chemical-Company-Website-SEP-Project
```

### 2. Create and activate a Virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/macOS
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```
### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Run the development server

```bash
python manage.py runserver
```

### 6. Access the application 

```bash
http://127.0.0.1:8000/
```

## Admin Access

Create a superuser to access a Admin panel

```bash
python manage.py createsuperuser
```

Admin panel:

```bash
http://127.0.0.1:8000/admin/

```

# Database

- Default database: SQLite
- Can be migrated to PostgreSQL for production use

# License

This project is developed for academic purposes under the Software Engineering Project (SEP).
All rights reserved.

# Author 

Saad Baig   
