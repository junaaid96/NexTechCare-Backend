# NexTechCare Backend API

A Django REST Framework based backend service for NexTechCare, providing various endpoints for user management, services, reviews, and more.

## Live Links

- Backend API: https://nextechcare-backend.onrender.com/
- Frontend Application: https://nextechcare.netlify.app/
- Frontend Repository: https://github.com/junaaid96/NexTechCare-Frontend

## Tech Stack

- Django 4.2.7
- Django REST Framework 3.14.0
- PostgreSQL Database
- JWT Authentication

## Features

- Custom User Authentication with JWT
- Role-based Authorization (Admin, Engineer, Customer)
- Service Management
- Review System
- Activity Tracking
- Contact Management

## API Endpoints

### Authentication

- `POST /profiles/register/` - Register a new user
- `POST /profiles/login/` - Login and get JWT tokens
- `POST /profiles/token/refresh/` - Refresh JWT token

### Profiles

- `GET /profiles/customers/` - List all customers (Admin only)
- `GET /profiles/engineers/` - List all engineers (Admin only)
- `GET /profiles/admins/` - List all admins (Admin only)

### Services

- `GET /services/` - List all services
- `POST /services/` - Create a new service (Engineer only)
- `GET /services/<id>/` - Get service details
- `PUT /services/<id>/` - Update service (Engineer only)
- `DELETE /services/<id>/` - Delete service (Engineer only)
- `POST /services/<id>/approve/` - Approve service (Admin only)

### Reviews

- `GET /reviews/` - List all reviews
- `POST /reviews/` - Create a new review (Customer only)
- `GET /reviews/<id>/` - Get review details
- `PUT /reviews/<id>/` - Update review (Owner only)
- `DELETE /reviews/<id>/` - Delete review (Owner only)

### Activities

- `GET /activities/` - List all activities (Admin only)

### Contact

- `POST /contacts/` - Send a contact message
- `GET /contacts/` - List all contact messages (Admin only)

## User Types and Permissions

1. **Admin (A)**
   - Can view all users
   - Can approve services
   - Can view all activities
   - Can view all contact messages

2. **Engineer (E)**
   - Can create/update/delete services
   - Can view assigned services

3. **Customer (C)**
   - Can create reviews
   - Can view services
   - Can send contact messages

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
```

2. Create and activate virtual environment:
```bash
python -m venv env
env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with following variables:
```plaintext
SECRET_KEY=your_secret_key
DB_USER=your_db_user
DB_PASS=your_db_password
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## API Authentication

The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:

```plaintext
Authorization: Bearer <your_access_token>
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## 2026 reimagine (CodeJBorg)

Live API: https://nextechcare-backend.vercel.app (Vercel, Python runtime) · DB: Neon Postgres

New: technology-support categories, booking tracker with SLA timeline (`/bookings/`), engineer Trust Score, AI Issue Triage (`/triage/`, Groq with rule-based fallback), admin stats (`/bookings/stats/`), bulk approve, engineer verification, `/health/`.

### Local
```bash
cp .env.example .env   # leave DATABASE_URL empty for SQLite
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python manage.py migrate && python manage.py runserver   # http://localhost:8000
python manage.py test
```
Migrations against Neon use the direct URL: `USE_UNPOOLED_DB=1 python manage.py migrate`.

Env vars (names): `SECRET_KEY`, `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `GROQ_API_KEY`, `GROQ_MODEL`.

Crafted by [CodeJBorg](https://junaidul.pro.bd/codejborg).
