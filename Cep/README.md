# 🏥 MedAdvisor - Smart Agentic Medical Advisor & Pharmacy

Flask-based pharmacy system with DB-driven symptom analysis, prescription validation, and pharmacist verification workflows.

## Key Features

- DB-driven symptom flow from `dataset_with_severity_and_prescription.csv` (`symptom -> disease -> severity -> medicines`)
- Severity rules: `serious -> Consult doctor`, `mild -> OTC/prescription split`, `unknown -> pharmacist escalation`
- Prescription upload + OCR/text extraction with automatic pharmacist escalation for unreadable files
- Medicine search flow with strict prescription checks and pharmacist fallback
- Order flow: all orders start as `pending_verification` and are queued for pharmacist verification
- Pharmacist dashboard APIs for requests, order decisions, prescription approvals, and user messaging

## Quick Start

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Runs on `http://127.0.0.1:5000`.

## Default Accounts

| Account | Email | Password |
|---------|-------|----------|
| Admin | admin@medadvisor.com | admin123 |
| Demo User | demo@medadvisor.com | demo123 |

## API Endpoints

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/profile` (auth)

### Medical
- `POST /api/medical/analyze` (auth) - symptom flow with severity branching
- `GET /api/medical/symptoms` - known symptoms from DB
- `POST /api/medical/upload-prescription` (auth) - prescription upload + validation/escalation
- `POST /api/medical/chat-order` (auth) - medicine ordering with prescription checks

### Medicines
- `GET /api/medicines/`
- `GET /api/medicines/:id`
- `POST /api/medicines/search-flow` (auth) - availability + prescription flow

### Orders
- `POST /api/orders/place` (auth) - creates order in `pending_verification`
- `GET /api/orders/my-orders` (auth)
- `GET /api/orders/track/:tracking_id`

### Admin / Pharmacist (admin auth)
- `GET /api/admin/dashboard`
- `GET /api/admin/pharmacist/requests`
- `GET /api/admin/pharmacist/orders`
- `PUT /api/admin/pharmacist/requests/:id/accept`
- `PUT /api/admin/pharmacist/requests/:id/reject` (reason required: `out_of_stock`, `invalid_prescription`, `not_available`)
- `PUT /api/admin/pharmacist/orders/:id/accept`
- `PUT /api/admin/pharmacist/orders/:id/reject`
- `PUT /api/admin/pharmacist/prescriptions/:id/approve`
- `POST /api/admin/pharmacist/users/:id/message`

## Dataset & Environment Variables

- `dataset_with_severity_and_prescription.csv` is loaded into DB tables for symptom and disease-medicine mappings.
- `medicine_dataset_with_price.csv` is used for medicine catalog seeding when available.
- Optional env vars:
  - `SYMPTOM_DATASET_PATH`
  - `MEDICINE_DATASET_PATH`
