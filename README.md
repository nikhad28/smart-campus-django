# 🎓 Campus AI Backend

A Smart Campus Management System Backend built using **Node.js**, **Express.js**, and **PostgreSQL**.

---

# 📌 Project Overview

Campus AI is an AI-powered Campus Management System that provides:

- 📚 Student Management
- 👨‍🏫 Faculty Management
- 📅 Biometric Attendance
- 📝 Marks Management
- 🤖 WhatsApp Chatbot
- 🧠 AI Career Recommendation
- 🔐 JWT Authentication

Students **do not have a web portal**.
Students interact only through the **WhatsApp Chatbot**.

Admin users include:
- Admin
- Faculty
- HOD
- Director

---

# 🛠️ Tech Stack

Backend
- Node.js
- Express.js

Database
- PostgreSQL

Authentication
- JWT
- bcrypt

API Testing
- Postman

Version Control
- Git
- GitHub

Future Integration
- WhatsApp Cloud API
- Face Recognition (Biometric Attendance)
- Machine Learning

---

# 📁 Project Structure

```
campus-ai-backend
│
├── src
│   ├── config
│   │   └── db.js
│   │
│   ├── controllers
│   │   ├── authController.js
│   │   └── studentController.js
│   │
│   ├── middleware
│   │   └── authMiddleware.js
│   │
│   ├── routes
│   │   ├── authRoutes.js
│   │   └── studentRoutes.js
│   │
│   ├── services
│   ├── models
│   ├── validators
│   ├── utils
│   └── app.js
│
├── server.js
├── package.json
├── .gitignore
└── README.md
```

---

# 🚀 Installation

## 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/campus-ai-backend.git
```

---

## 2. Open Project

```bash
cd campus-ai-backend
```

---

## 3. Install Packages

```bash
npm install
```

---

## 4. Create .env File

Create a file named `.env`

Example:

```env
PORT=5000

DB_HOST=localhost
DB_PORT=5432
DB_NAME=campus_ai
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD

JWT_SECRET=YOUR_SECRET_KEY
```

---

## 5. Start Server

```bash
npm run dev
```

Server:

```
http://localhost:5000
```

---

# 📦 APIs Implemented

## Authentication

| Method | Endpoint |
|---------|----------|
| POST | /api/auth/login |

---

## Students

| Method | Endpoint |
|---------|----------|
| GET | /api/students |
| GET | /api/students/:id |
| POST | /api/students |
| PUT | /api/students/:id |
| DELETE | /api/students/:id |

---

# 🗄️ Database

Current Schemas

- academic
- attendance
- marks
- chatbot
- ai
- auth

---

# 📅 Development Roadmap

## ✅ Phase 1

- PostgreSQL Setup
- Express Setup
- Student CRUD
- Authentication

---

## 🚧 Phase 2

- Faculty CRUD
- Subject CRUD

---

## 🚧 Phase 3

Attendance Module

- Face Recognition Attendance
- Attendance Reports
- Parent Notification

---

## 🚧 Phase 4

Marks Management

- Add Marks
- Update Marks
- Result Generation
- SGPA
- CGPA

---

## 🚧 Phase 5

Dashboard

- Faculty Dashboard
- HOD Dashboard
- Director Dashboard

---

## 🚧 Phase 6

WhatsApp Chatbot

Student can ask:

- My attendance
- My marks
- My result
- Notices
- Timetable

---

## 🚧 Phase 7

AI Career Recommendation

Input:

- Semester 1–6 Marks
- Attendance
- Performance

Output:

- Software Development
- Data Science
- AI/ML
- Cyber Security
- Cloud Computing
- Networking

---

# 👥 Team Members

| Name | Responsibility |
|------|----------------|
| Member 1 | Authentication & Student Module |
| Member 2 | Faculty & Subject Module |
| Member 3 | Attendance Module |
| Member 4 | Marks, AI & WhatsApp Chatbot |

---

# ⚠️ Important

Do NOT upload:

- `.env`
- `node_modules`

Before pushing:

```bash
git status
```

If everything looks correct:

```bash
git add .
git commit -m "Your commit message"
git push
```

---

# 📄 License

This project is developed as a Final Year Engineering Major Project.
