# 📝 High-Performance Content Collaboration Platform (HCCP)

A high-performance content collaboration platform with **role-based access, version control, optimized caching, and analytics**. Built using **Django, PostgreSQL, Redis, and Docker**.

---

## 🚀 Features

- **RESTful APIs** for content management  
- **Role-Based Access Control (RBAC)** for Admins, Authors, and Collaborators  
- **Article Version Control & Activity Logs** for tracking edits  
- **Optimized Caching & Rate Limiting** using Redis  
- **Secure JWT Authentication**

---

## ⚙️ Setup Instructions (Docker)

### 🐍 1️⃣ Clone the Repository

```bash
git clone https://github.com/Dev-ShivamKumarSinha/HCCP.git
cd HCCP
```

### 📌 2️⃣ Setup Environment Variables

Create an `.env` file using the example provided:

```bash
cp .env.example .env
```

Update database details inside `.env`:

```
SECRET_KEY=django_sample_secret
DEBUG=true_or_false

DATABASE_URL=postgres://<user>:<password>@<db_host>:<port>/<db_name>
DATABASE_NAME=db_name
DATABASE_USERNAME=db_username
DATABASE_PASSWORD=db_password
DATABASE_HOST=db_host
DATABASE_PORT=db_port

REDIS_HOST=redis
REDIS_PORT=6379
```

### 🐳 3️⃣ Build and Run the Project with Docker

```bash
docker-compose up -d --build
```

This starts:
- **Backend** at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Redis** at `localhost:6379`
- **PostgreSQL** (external DB, configured in `.env`)
  
> **Important**: An **admin user** is automatically created with the following credentials when you run the above command:
> - **Username**: `admin`
> - **Password**: `adminpassword`
> - **Email**: `admin@example.com`

### 📌 4️⃣ Stop the Project 

To stop the running containers:

```bash
docker-compose down
```

---

## 🔐 Authentication

### **1️⃣ Register (`POST /api/register/`)**

**Request**:
```json
{
    "username": "newuser",
    "password": "securepassword",
    "email": "newuser@example.com"
}
```

**Response**:
```json
{
   "detail": "User registered successfully!"
}
```
## 🛠 Role Assignment for New Users
- Users are not assigned to any group (Author or Collaborator) by default.
- A user becomes an "Author" if they create an article (POST /api/articles/).
- A user becomes a "Collaborator" if an existing Author/Admin adds them as a collaborator (POST /api/articles/<id>/collaborators/).

  **✅ This ensures dynamic role assignment instead of fixed roles at registration.**

### **2️⃣ Login (`POST /api/login/`)**

**Request**:
```json
{
    "username": "admin",
    "password": "adminpassword"
}
```

**Response**:
```json
{
    "access": "your_jwt_access_token",
    "refresh": "your_jwt_refresh_token"
}
```

> **Use the `access` token in all API requests**:
```bash
Authorization: Bearer your_jwt_access_token
```

---

## 🔥 API Documentation

### 1️⃣ Articles

| Method | Endpoint                          | Description              | Auth Required |
|-------:|:----------------------------------|:-------------------------|:-------------:|
| **POST**   | `/api/articles/`                  | Create an article        | ✅ Yes         |
| **GET**    | `/api/articles/<id>`             | Fetch article details    | ✅ Yes         |
| **PUT**    | `/api/articles/<id>`             | Update article           | ✅ Yes         |
| **DELETE** | `/api/articles/<id>`             | Soft delete article      | ✅ Yes         |
| **POST**   | `/api/articles/<id>/rollback`    | Restore article          | ✅ Yes         |
| **POST**   | `/api/articles/<id>/collaborators` | Add/Remove collaborators | ✅ Yes         |

**Example Response for `GET /api/articles/1`:**
```json
{
    "data": {
        "id": 1,
        "title": "Test Article",
        "body": "Hello World",
        "author": "testuser",
        "tags": "example,test",
        "created_at": "2025-01-29T00:00:00Z",
        "updated_at": "2025-01-29T00:00:00Z"
    }
}
```

### 2️⃣ Version Control & Analytics

| Method | Endpoint                               | Description                      | Auth Required  |
|-------:|:---------------------------------------|:--------------------------------|:--------------:|
| **GET**    | `/api/articles/<id>/history/`          | Get article version history      | ✅ Yes          |
| **GET**    | `/api/analytics/user-activity`        | Admin: Fetch user activity logs  | ✅ Admin Only   |
| **GET**    | `/api/analytics/user-edits`           | Admin: Total edits per user      | ✅ Admin Only   |

**Example Response for `GET /api/articles/1/history/`:**
```json
[
    {
        "version": 1,
        "body": "First Version",
        "updated_at": "2025-01-29T00:00:00Z",
        "updated_by": "testuser"
    }
]
```

---

## 📌 Checking Real-Time Server Logs
To monitor the backend server logs in real-time, run:
```bash
docker-compose logs -f backend
```
✅ This continuously streams logs from the backend container, including:
- API requests
- Errors & exceptions
- Debugging information (print() statements inside views)

### 🔄 Restarting Server & Watching Logs
If needed, restart the backend and check logs simultaneously:
```bash
docker-compose restart backend && docker-compose logs -f backend
```

## 🛠 Testing Instructions

### ✅ Postman API Testing

1. **Login** (`POST /api/login/`) and copy the `access` token.  
2. Use the `access` token for API requests (`Authorization: Bearer your_jwt_access_token`).  
3. Test endpoints like `GET /api/articles/1` in Postman.

---

## 🛡 Security Features

- **JWT Authentication** (Secure token-based login)  
- **CSRF Protection** (For web clients)  
- **Data Validation & Sanitization** (Prevents SQL Injection & XSS)  
- **Role-Based Access Control (RBAC)** (Admins control access)  
- **Rate Limiting** (Prevents API abuse)  
