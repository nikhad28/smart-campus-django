```md
# 🏫 Smart Campus Management System

A complete campus management system for **AIKTC (Anjuman-I-Islam's Kalsekar Technical Campus)** built with **Django**, **Supabase**, and **Bootstrap**.

---

## 📌 Project Overview

Smart Campus is a role-based platform for managing:

- 👨‍🎓 Students
- 👨‍🏫 Faculty
- 👔 HOD
- 💼 TPO (Training & Placement Officer)
- 👨‍💼 Admin
- 👨‍👩‍👦 Parents

---

## 🛠️ Tech Stack

### Backend
- Django 5.0
- Supabase (PostgreSQL)
- Django REST Framework

### Frontend
- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- AOS (Animations)

### Authentication
- Session-based (Admin)
- OTP-based (Students)
- Password-based (TPO)

---

## ✨ Features

### 🔐 Authentication
- Admin Login (user_id + password)
- Student Login (WhatsApp number + OTP)
- TPO Login (user_id + password)

### 👨‍🎓 Student Module
- View courses
- Check attendance
- View results

### 💼 TPO Module
- Manage companies
- Track placements
- View applications

### 🏫 Admin Module
- Manage all users
- Add/Edit/Delete students, faculty, HOD, TPO
- Department management

### 🎨 UI Features
- Bottle Green + White Theme
- Glassmorphism cards
- 3D hover effects
- Floating animations
- Fully responsive

### 📱 Pages
- Index Landing Page
- Admin Login & Dashboard
- Student Login & Dashboard
- TPO Login & Dashboard
- Role-based dashboards

---

## 📁 Project Structure

```
smart-campus-django/
│
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
│
├── config/
│   ├── settings.py
│   └── urls.py
│
├── core/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── supabase_client.py
│
├── otp_app/
│   ├── models.py
│   └── views.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── student_login.html
│   ├── student_verify_otp.html
│   ├── student_dashboard.html
│   ├── tpo_login.html
│   └── tpo_dashboard.html
│
├── static/
│   ├── css/
│   └── js/
│
└── media/
```

---

## 🚀 Installation

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/smart-campus-django.git
cd smart-campus-django
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` File

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Start Server

```bash
python manage.py runserver
```

Server will run at:

```
http://localhost:8000
```

---

## 📦 Supabase Tables

### `user_account`
- user_id (UUID, PK)
- username (VARCHAR, UNIQUE)
- password_hash (VARCHAR)
- faculty_id (VARCHAR)
- role_id (INTEGER)
- is_active (BOOLEAN)

### `student`
- student_id (UUID, PK)
- roll_no (VARCHAR)
- full_name (VARCHAR)
- gender (VARCHAR)
- dob (DATE)
- whatsapp_no (VARCHAR)
- admission_year (INTEGER)
- department_id (VARCHAR)
- semester_id (INTEGER)
- division_id (VARCHAR)

### `tpo`
- tpo_id (UUID, PK)
- user_id (VARCHAR, UNIQUE)
- password_hash (VARCHAR)
- full_name (VARCHAR)
- email (VARCHAR, UNIQUE)
- phone (VARCHAR)
- department (VARCHAR)
- is_active (BOOLEAN)

---

## 📋 Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Student | WhatsApp Number | OTP (console) |
| TPO | tpo_user | tpo12345 |

---

## 🗺️ URL Routes

| URL | Page |
|-----|------|
| `/` | Index Landing Page |
| `/admin-login/` | Admin Login |
| `/admin-dashboard/` | Admin Dashboard |
| `/student-login/` | Student Login |
| `/student-verify-otp/` | Verify OTP |
| `/student-dashboard/` | Student Dashboard |
| `/tpo-login/` | TPO Login |
| `/tpo-dashboard/` | TPO Dashboard |

---

## 📸 Screenshots

### Index Page
- Hero section with college badge
- Features cards with 3D hover
- Events & Activities section
- Departments section
- Role selection cards

### Admin Dashboard
- User management
- Department management
- Quick actions

### Student Dashboard
- View courses
- Check attendance
- View results

### TPO Dashboard
- Company management
- Placement tracking
- Application management

---

## 🎨 Theme Colors

| Color Name | Hex Code |
|------------|----------|
| Bottle Green | `#004d40` |
| Light Green | `#00695c` |
| Dark Green | `#00332a` |
| Gold Accent | `#ffd93d` |
| White | `#ffffff` |
| Cream | `#f5f0eb` |

---

## 📅 Development Roadmap

### ✅ Completed
- Admin Login & Dashboard
- Student Login (OTP-based)
- TPO Login & Dashboard
- Index Landing Page
- Features & Events Section
- Departments Section
- Supabase Integration

### 🚧 In Progress
- Faculty Module
- HOD Module
- Parents Module

### 📝 Future Plans
- Attendance System
- Marks Management
- Placement Module
- AI Chatbot
- WhatsApp Integration

---

---

## ⚠️ Important Notes

1. **OTP is printed on console** — actual SMS/WhatsApp integration pending
2. **Supabase is used as database** — PostgreSQL on cloud
3. **No production deployment yet** — development only

---

## 📄 License

This project is developed for educational purposes.

---

## 📞 Contact

- **Developer:** Nikhad Shaikh , Insha Shakeel , Munira Lmbuwale , Iqra Shaikh
- **College:** AIKTC (Anjuman-I-Islam's Kalsekar Technical Campus)

---
---

## 📁 `requirements.txt`

Django==5.0.6
djangorestframework==3.15.1
django-cors-headers==4.3.1
psycopg2-binary==2.9.9
python-dotenv==1.0.1
supabase==2.5.1
bcrypt==4.1.2
Pillow==10.3.0
django-filter==24.2
