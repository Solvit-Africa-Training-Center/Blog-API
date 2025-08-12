#  Blog API

##  Project Overview

The **Blog API** is a backend system for a professional blogging platform, built with **Django** and **Django REST Framework (DRF)**.  
It supports **JWT authentication**, **role-based permissions**, **content management**, and **enterprise-level security features**.  
Think of it as a secure, API-only backend similar to **Medium** or **WordPress**, but with advanced features like **rate limiting**, **historical data downloads**, and **OANDA-style bulk data export**.



##  Features
- **User Authentication**
  - Registration & login
  - JWT token-based authentication
  - Secure token management
- **Blog Post Management**
  - CRUD operations
  - Public & private visibility
  - Rich metadata support
- **Category & Tag Management**
  - Categories and tags for posts
  - Filtering by category, tag, and author
- **Comment System**
  - Nested comments
  - Author-only edit permissions
- **Advanced Security**
  - Role-based permissions
  - Rate limiting & throttling
  - Secure file download endpoint
- **Search, Filtering, Pagination**
  - Category/tag filtering
  - Full-text search
  - Custom pagination
- **API Documentation**
  - Swagger UI (drf-spectacular)
  - Postman collection



##  Technology Stack
- **Backend:** Django 4.x, Django REST Framework
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Database:** SQLite (development), PostgreSQL (production)
- **Filtering:** django-filter
- **Documentation:** drf-spectacular (Swagger)
- **Testing:** Django TestCase, DRF APITestCase




