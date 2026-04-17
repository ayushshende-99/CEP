# 🏥 MedAdvisor - Smart Agentic Medical Advisor & Pharmacy

AI-powered health guidance and online pharmacy web application built with a multi-agent architecture.

## Features

- **🤖 AI Symptom Analysis** - Describe symptoms in natural language to get likely disease predictions and medicine suggestions
- **💊 Online Pharmacy** - Browse 18+ medicines across 7 categories with search and filters
- **🛒 Cart & Checkout** - Add to cart, simulated payment, and order placement
- **📦 Order Tracking** - Real-time order status with visual timeline (Ordered → Confirmed → Packed → Shipped → Out for Delivery → Delivered)
- **🔒 JWT Authentication** - Secure signup/login system
- **🛠️ Admin Dashboard** - View users, manage orders, medicine inventory CRUD, revenue stats

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Flask (Python) |
| Database | SQLite (via SQLAlchemy) |
| Auth | JWT (PyJWT) |
| AI Engine | Dataset-trained Bernoulli Naive Bayes disease prediction |

## Project Structure

```
Cep/
├── backend/
│   ├── app.py                # Main Flask application
│   ├── config.py             # Configuration
│   ├── models.py             # SQLAlchemy models
│   ├── requirements.txt      # Python dependencies
│   ├── agents/
│   │   ├── medical_ai.py     # Medical AI Agent (12+ conditions)
│   │   ├── ecommerce.py      # E-commerce Agent
│   │   ├── tracking.py       # Tracking Agent
│   │   └── admin.py          # Admin Agent
│   └── routes/
│       ├── auth.py           # Auth routes (JWT)
│       ├── medical.py        # Symptom analysis routes
│       ├── medicines.py      # Medicine catalog routes
│       ├── orders.py         # Order & tracking routes
│       └── admin.py          # Admin routes
└── frontend/
    ├── index.html            # Home page
    ├── login.html            # Login
    ├── register.html         # Registration
    ├── dashboard.html        # AI Chat dashboard
    ├── shop.html             # Medicine shop
    ├── cart.html             # Shopping cart & checkout
    ├── tracking.html         # Order tracking
    ├── admin.html            # Admin panel
    ├── css/styles.css        # Design system
    └── js/
        ├── app.js            # Core logic & API helpers
        ├── auth.js           # Login/Register logic
        ├── chat.js           # AI chatbot logic
        ├── shop.js           # Shop filtering & search
        ├── cart.js           # Cart & checkout logic
        ├── tracking.js       # Order tracking logic
        └── admin.js          # Admin dashboard logic
```

## Quick Start

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the server
```bash
python app.py
```

### 3. Open in browser
``` 
    http://127.0.0.1:5000
```

## Default Accounts

| Account | Email | Password |
|---------|-------|----------|
| Admin | admin@medadvisor.com | admin123 |
| Demo User | demo@medadvisor.com | demo123 |

## API Endpoints

### Auth
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/profile` - Get profile (auth required)

### Medical AI
- `POST /api/medical/analyze` - Analyze symptoms (auth required)
- `GET /api/medical/symptoms` - List supported symptoms

### Medicines
- `GET /api/medicines/` - List all medicines
- `GET /api/medicines/:id` - Get medicine details

### Orders
- `POST /api/orders/place` - Place order (auth required)
- `GET /api/orders/my-orders` - User's orders (auth required)
- `GET /api/orders/track/:tracking_id` - Track order

### Admin (admin auth required)
- `GET /api/admin/dashboard` - Dashboard stats
- `GET /api/admin/users` - All users
- `GET /api/admin/orders` - All orders
- `PUT /api/admin/orders/:id/advance` - Advance order status
- `POST /api/admin/medicines` - Add medicine
- `PUT /api/admin/medicines/:id` - Update medicine
- `DELETE /api/admin/medicines/:id` - Delete medicine

## Multi-Agent Architecture

1. **Medical AI Agent** - Extracts symptoms from natural language and ranks likely diseases using a model trained from the disease-symptom dataset
2. **E-commerce Agent** - Handles cart validation, stock management, order placement, and tracking ID generation
3. **Tracking Agent** - Manages 6-stage order lifecycle with timeline visualization
4. **Admin Agent** - Provides dashboard analytics, user management, and inventory CRUD

## Safety & Disclaimer

> ⚠️ This application provides AI-generated health suggestions only. It is NOT a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional before taking any medication.

## ML Dataset Setup

- The disease predictor trains from `Final_Augmented_dataset_Diseases_and_Symptoms.csv`.
- Medicine recommendations are enriched from `medical_question_answer_dataset_50000.csv`.
- By default it looks in `Cep/backend/data/` first, then falls back to `/Users/rutujabarde/Downloads/Final_Augmented_dataset_Diseases_and_Symptoms.csv`.
- For medicine recommendation data, it looks in `Cep/backend/data/` first, then falls back to `/Users/rutujabarde/Downloads/medical_question_answer_dataset_50000.csv`.
- You can also set `MEDICAL_DATASET_PATH` to point to the dataset explicitly.
- You can set `MEDICAL_QA_DATASET_PATH` to point to the medicine recommendation dataset explicitly.
- The trained model is cached automatically in `Cep/backend/data/disease_prediction_model.pkl` after the first run.
