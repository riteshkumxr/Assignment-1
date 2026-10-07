# Bulk Certificate Generator Backend API

A high-performance backend API built with **FastAPI**, **SQLAlchemy**, and **ReportLab** designed to accept bulk certificate generation requests for hundreds or thousands of recipients, process them efficiently with granular failure isolation, track real-time progress, and retrieve generated certificates individually or as bulk ZIP archives.

---

## Table of Contents

- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Tech Stack & Rationale](#tech-stack--rationale)
- [Setup & Installation](#setup--installation)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [API Walkthrough & Examples](#api-walkthrough--examples)
  - [1. Submit a Bulk Generation Job](#1-submit-a-bulk-generation-job)
  - [2. Check Job Status & Progress](#2-check-job-status--progress)
  - [3. Download an Individual Certificate](#3-download-an-individual-certificate)
  - [4. Download All Certificates as ZIP](#4-download-all-certificates-as-zip)
  - [5. List All Jobs](#5-list-all-jobs)
- [Important Implementation & Design Decisions](#important-implementation--design-decisions)
- [Handling Failures & Edge Cases](#handling-failures--edge-cases)
- [Interview & Architecture Talking Points](#interview--architecture-talking-points)

---

## Key Features

1. **True Bulk Generation**: Submit batches of recipients in a single API call with automatic background processing.
2. **Partial Failure Isolation**: A failure while generating one certificate (e.g., bad data or rendering exception) **never** prevents other valid certificates from being generated.
3. **Real-time Progress Tracking**: Granular counters (`total_recipients`, `processed_count`, `success_count`, `failed_count`) updated incrementally with per-recipient statuses and detailed failure reasons.
4. **Predefined Professional Certificate Template**: Vector-rendered landscape A4 PDF with multi-tier borders, gold seal, crisp typography, issuer signatures, dynamic recipient attributes, and embedded verification QR codes.
5. **Flexible Retrieval**: Download individual PDF certificates or download all completed certificates in a batch as a single compressed ZIP archive.
6. **96%+ Test Coverage**: 26 automated unit and integration tests verifying creation, input validation, template rendering, failure isolation, and downloads.

---

## System Architecture

```text
 Client (Browser / API Client)
       │
       ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ FastAPI REST API Layer                                      │
 │   • POST /api/v1/jobs              (Accepts batch payload)  │
 │   • GET  /api/v1/jobs/{id}         (Status & progress)      │
 │   • GET  /api/v1/jobs/{id}/download-zip (Bulk ZIP export)   │
 │   • GET  /api/v1/certificates/{id}/download (Single PDF)    │
 └──────────────────────────────┬──────────────────────────────┘
                                │
               Dispatches Background Task
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Background Worker (JobService.process_job_worker)           │
 │   • Uses isolated database session                          │
 │   • Loops through recipients inside try/catch error boundary│
 │   • Generates PDF via ReportLab engine                      │
 │   • Commits incremental progress per record                 │
 └───────────────┬──────────────────────────────┬──────────────┘
                 │                              │
                 ▼                              ▼
 ┌──────────────────────────────┐ ┌────────────────────────────┐
 │ Relational Database          │ │ File Storage System        │
 │ (SQLAlchemy / SQLite WAL)    │ │ (storage/certificates/     │
 │   • jobs table               │ │    {job_id}/{cert_id}.pdf) │
 │   • certificates table       │ └────────────────────────────┘
 └──────────────────────────────┘
```

---

## Tech Stack & Rationale

| Component | Choice | Rationale |
| :--- | :--- | :--- |
| **Framework** | **FastAPI** | High-performance asynchronous execution, automatic interactive OpenAPI docs (`/docs`), and native `BackgroundTasks`. |
| **Validation** | **Pydantic v2** | Strict type-safety, fast C-based parsing, email format validation, and expressive custom validators. |
| **Database ORM** | **SQLAlchemy 2.0** | Industry standard relational ORM with clear session management, relationships, and clean database abstraction. |
| **Database** | **SQLite (WAL mode)** | Frictionless local setup with zero external Docker or daemon dependencies; WAL mode enables safe concurrent reads and background writes. Decoupled via `DATABASE_URL` so switching to PostgreSQL is a 1-line configuration change. |
| **PDF Generation** | **ReportLab 5.0** | Pure Python vector graphics engine; produces crisp, authentic PDFs without heavy system dependencies (such as Chrome, Weasyprint, or Cairo DLLs). |
| **QR Code Engine**| **qrcode + Pillow** | Dynamically embeds scannable verification QR codes directly onto the certificate canvas. |
| **Testing** | **pytest + pytest-cov** | Fast, robust test framework with fixtures and code coverage analysis. |

---

## Setup & Installation

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- `pip`

### 2. Clone / Navigate to Project Directory
```bash
cd scratch/bulk-cert-generator
```

### 3. Create and Activate Virtual Environment (Optional but Recommended)
```bash
python -m venv venv

# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

Start the local server using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Running Tests

Run the complete test suite with verbose output:

```bash
python -m pytest tests/ -v
```

To run with full code coverage reporting:

```bash
python -m pytest --cov=app --cov-report=term-missing tests/
```

**Test Coverage Summary**:
```
Name                             Stmts   Miss  Cover
----------------------------------------------------
app/api/routes/certificates.py      29      0   100%
app/api/routes/jobs.py              46      1    98%
app/services/validator.py           21      0   100%
app/services/generator.py          168      3    98%
app/services/job_service.py        112     15    87%
app/main.py                         20      0   100%
app/config.py                       19      0   100%
TOTAL                              591     25    96%
```

---

## API Walkthrough & Examples

### 1. Submit a Bulk Generation Job
**Endpoint**: `POST /api/v1/jobs`  
**Status Code**: `202 Accepted`

#### Request:
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "event_title": "Advanced Microservices Architecture",
    "issuer_name": "Cloud Native Institute",
    "issue_date": "2026-10-07",
    "recipients": [
      {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "custom_data": {"grade": "A+", "honors": "Distinction"}
      },
      {
        "name": "John Smith",
        "email": "john.smith@example.com",
        "custom_data": {"grade": "A"}
      }
    ]
  }'
```

#### Response (`202 Accepted`):
```json
{
  "id": "4b1049ea-9f8d-4b92-8051-93db03493e87",
  "event_title": "Advanced Microservices Architecture",
  "issuer_name": "Cloud Native Institute",
  "issue_date": "2026-10-07",
  "status": "PENDING",
  "total_recipients": 2,
  "processed_count": 0,
  "success_count": 0,
  "failed_count": 0,
  "created_at": "2026-10-07T04:30:00Z",
  "updated_at": "2026-10-07T04:30:00Z",
  "completed_at": null
}
```

---

### 2. Check Job Status & Progress
**Endpoint**: `GET /api/v1/jobs/{job_id}`  
**Status Code**: `200 OK`

Supports optional query filters:
- `?recipient_status=COMPLETED` or `?recipient_status=FAILED`
- `?limit=100&offset=0` for pagination of large recipient sets.

#### Request:
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/4b1049ea-9f8d-4b92-8051-93db03493e87"
```

#### Response:
```json
{
  "id": "4b1049ea-9f8d-4b92-8051-93db03493e87",
  "event_title": "Advanced Microservices Architecture",
  "issuer_name": "Cloud Native Institute",
  "issue_date": "2026-10-07",
  "status": "COMPLETED",
  "total_recipients": 2,
  "processed_count": 2,
  "success_count": 2,
  "failed_count": 0,
  "created_at": "2026-10-07T04:30:00Z",
  "updated_at": "2026-10-07T04:30:02Z",
  "completed_at": "2026-10-07T04:30:02Z",
  "download_zip_url": "http://localhost:8000/api/v1/jobs/4b1049ea-9f8d-4b92-8051-93db03493e87/download-zip",
  "recipients": [
    {
      "id": "e816a7cb-c19b-4fa6-848e-ee9c314b9868",
      "job_id": "4b1049ea-9f8d-4b92-8051-93db03493e87",
      "recipient_name": "Jane Doe",
      "recipient_email": "jane.doe@example.com",
      "status": "COMPLETED",
      "download_url": "http://localhost:8000/api/v1/certificates/e816a7cb-c19b-4fa6-848e-ee9c314b9868/download",
      "error_message": null,
      "custom_data": {"grade": "A+", "honors": "Distinction"},
      "created_at": "2026-10-07T04:30:00Z",
      "updated_at": "2026-10-07T04:30:01Z"
    },
    {
      "id": "7fa1bc82-0129-4dbe-a1c0-0e104e76a6d3",
      "job_id": "4b1049ea-9f8d-4b92-8051-93db03493e87",
      "recipient_name": "John Smith",
      "recipient_email": "john.smith@example.com",
      "status": "COMPLETED",
      "download_url": "http://localhost:8000/api/v1/certificates/7fa1bc82-0129-4dbe-a1c0-0e104e76a6d3/download",
      "error_message": null,
      "custom_data": {"grade": "A"},
      "created_at": "2026-10-07T04:30:00Z",
      "updated_at": "2026-10-07T04:30:02Z"
    }
  ]
}
```

---

### 3. Download an Individual Certificate
**Endpoint**: `GET /api/v1/certificates/{certificate_id}/download`  
**Response Header**: `Content-Type: application/pdf`

```bash
curl -O -J "http://localhost:8000/api/v1/certificates/e816a7cb-c19b-4fa6-848e-ee9c314b9868/download"
```
Downloads `Certificate_Jane_Doe_e816a7cb.pdf`.

---

### 4. Download All Certificates as ZIP
**Endpoint**: `GET /api/v1/jobs/{job_id}/download-zip`  
**Response Header**: `Content-Type: application/zip`

```bash
curl -O -J "http://localhost:8000/api/v1/jobs/4b1049ea-9f8d-4b92-8051-93db03493e87/download-zip"
```
Downloads `certificates_4b1049ea.zip` containing all generated PDF certificates.

---

### 5. List All Jobs
**Endpoint**: `GET /api/v1/jobs?page=1&page_size=20`

```bash
curl -X GET "http://localhost:8000/api/v1/jobs?page=1&page_size=10"
```

---

## Important Implementation & Design Decisions

### 1. Asynchronous Background Processing
- **Problem**: Generating hundreds of PDF certificates takes several seconds or minutes, which would exceed HTTP gateway timeouts (typically 30–60s) if handled synchronously.
- **Solution**: The API accepts the request, persists initial job and recipient records with status `PENDING`, and returns `202 Accepted` immediately with the `job_id`. FastAPI's `BackgroundTasks` delegates the rendering pipeline to an asynchronous background worker (`JobService.process_job_worker`).
- **Database Session Isolation**: The background worker instantiates its own dedicated `SessionLocal()` rather than reusing the request-scoped session, guaranteeing that background execution is safe from request connection termination.

### 2. Failure Isolation Strategy (Resilience)
- **Problem**: In a batch of 500 recipients, 1 recipient might have corrupted unicode characters, illegal control bytes, or cause an edge-case rendering exception.
- **Design Decision**: The worker wraps every individual recipient generation inside an isolated `try...except` block.
- **Granular Status Tracking**:
  - Valid recipients are updated to `status = "COMPLETED"`.
  - Failing recipients are updated to `status = "FAILED"` with the exact exception recorded in `error_message`.
  - The job status transitions to `PARTIALLY_COMPLETED` (if some succeeded) or `FAILED` (if all failed).
  - Valid certificates are still downloadable and included in the bulk ZIP archive.

### 3. Incremental Database Commits
- Instead of committing once at the very end of the batch, the worker commits after each certificate generation.
- **Benefit**: Clients polling `GET /api/v1/jobs/{job_id}` see real-time updates for `processed_count`, `success_count`, and `failed_count`.

### 4. Vector PDF Rendering via ReportLab
- Alternative tools like `wkhtmltopdf` or headless Puppeteer/Playwright require external binaries and high memory overhead (~100–300MB per render).
- ReportLab runs natively in pure Python, generates lightweight vector PDFs (~4KB per file), runs in under 15ms per certificate, and cleanly integrates dynamic QR code generation.

---

## Handling Failures & Edge Cases

| Scenario | System Behavior | HTTP Response |
| :--- | :--- | :--- |
| **Empty recipient list** | Rejected by Pydantic validator before database write | `422 Unprocessable Entity` |
| **Malformed email address** | Rejected by schema validation | `422 Unprocessable Entity` |
| **Empty or whitespace names** | Stripped and validated; fails schema validation | `422 Unprocessable Entity` |
| **Runtime recipient generation error** | Trapped in worker error boundary; job marked `PARTIALLY_COMPLETED`, error saved | Job completes; `GET /jobs/{id}` reveals failing item and error |
| **Downloading in-progress cert** | Detects `PENDING` or `PROCESSING` status | `409 Conflict` |
| **Downloading failed cert** | Explains why generation failed | `400 Bad Request` |
| **Downloading non-existent cert/job** | Returns standard error message | `404 Not Found` |
| **Downloading ZIP with 0 success** | Prevents empty ZIP creation | `400 Bad Request` |

---

## Interview & Architecture Talking Points

When discussing or extending this project during an interview:

1. **Scaling to Multi-Node Distributed Workers**:
   - Currently, FastAPI `BackgroundTasks` executes in-process, which is ideal for single-instance deployments and zero external dependencies.
   - For a distributed system scaling to millions of certificates, replace `BackgroundTasks` with **Celery** or **ARQ** backed by **Redis** or **RabbitMQ**. The existing `JobService.process_job_worker` function is decoupled and ready to be decorated with `@celery_app.task`.

2. **Storage Decoupling (AWS S3 / GCP Cloud Storage)**:
   - Currently, files are stored on local disk under `storage/certificates/`.
   - To support cloud object storage, implement a `StorageService` interface with `upload_file()` and `generate_presigned_url()` methods.

3. **Template Engine Extensibility**:
   - Currently, a single elegant predefined template is used.
   - To support multiple templates, add a `template_id` field to `GenerationJob`, and introduce a Template Registry (`template_factory.get(template_id)`).

4. **Webhooks / Event Notifications**:
   - Clients could provide an optional `webhook_url` in `JobCreate`. Upon job completion, the worker dispatches an HTTP POST request to notify the client automatically.
