# BidSure AI — Module Contracts

## 1. Purpose

This document defines the standard communication rules and input/output formats between different modules of the BidSure AI platform.

The goal is to ensure that different team members can work independently and their modules can later be integrated without major changes.

The current development team consists of:

1. Core Backend
2. Document Intelligence
3. Verification Providers

Future modules such as the Compliance Engine, Risk Engine, AI Recommendation Engine, and Frontend will follow these same principles.

---

# 2. Core Development Principle

Each module must have:

- A clearly defined responsibility.
- Clearly defined inputs.
- Clearly defined outputs.
- Minimal dependency on other modules.
- Independent testability.
- No unnecessary modification of another team's code.
- Predictable error handling.
- Consistent naming conventions.

The overall system flow will eventually be:

```text
Bidder / Tender
       │
       ▼
Document Upload
       │
       ▼
Document Intelligence
       │
       ▼
Structured Extracted Data
       │
       ▼
Verification Providers
       │
       ▼
Verification Results
       │
       ▼
Cross-Verification
       │
       ▼
Compliance Engine
       │
       ▼
Compliance Result
       │
       ▼
Risk & Compliance Scoring
       │
       ▼
AI Recommendation
       │
       ▼
Procurement Officer Decision
```

---

# 3. Module Responsibilities

## 3.1 Core Backend

### Owner

Core Backend Team

### Responsibilities

The Core Backend is responsible for:

```text
FastAPI application
Configuration management
Database connection
Database models
Pydantic schemas
API routes
Authentication
Authorization
Integration between modules
Workflow orchestration
Error handling
Logging
```

### Main folders

```text
backend/app/
├── main.py
├── core/
├── database/
├── models/
├── schemas/
├── api/
└── repositories/
```

### The Core Backend should NOT initially implement:

```text
OCR algorithms
Document extraction logic
Document classification logic
Government verification logic
AI experimentation logic
```

Those modules should be developed independently and integrated later.

---

## 3.2 Document Intelligence

### Owner

Document Intelligence Team

### Responsibility

The Document Intelligence module answers:

> What information exists inside the uploaded document?

It is responsible for:

```text
PDF text extraction
OCR for scanned documents
Document classification
Field extraction
Structured output generation
```

### Main folder

```text
backend/app/services/
└── document_processing/
    ├── pdf_extractor.py
    ├── ocr_service.py
    ├── document_classifier.py
    ├── field_extractor.py
    └── processor.py
```

### The Document Intelligence module should NOT:

```text
Decide bidder qualification
Perform compliance scoring
Make procurement decisions
Access the main database directly
Depend on FastAPI routes for testing
```

It should be independently testable.

Example:

```python
result = process_document("sample_documents/gst_certificate.pdf")
```

---

## 3.3 Verification Providers

### Owner

Verification Provider Team

### Responsibility

The Verification Provider module answers:

> Is this identifier or information valid according to the relevant verification source?

Examples include:

```text
GST
PAN
Udyam/MSME
EPFO
ESIC
Startup India
NSIC
Debarment
```

### Initial implementation

Initially, implement:

```text
GST
PAN
UDYAM
```

### Main folder

```text
backend/app/providers/
├── base.py
├── gst_provider.py
├── pan_provider.py
├── udyam_provider.py
└── mock_data_provider.py
```

The verification team should initially use mock data.

Example:

```python
result = verify_gst("27ABCDE1234F1Z5")
```

The provider should work independently without requiring:

```text
Database
FastAPI server
Frontend
Document processing module
```

---

# 4. Common Status Rules

Different modules use different status values.

These statuses must NOT be mixed.

---

## 4.1 Processing Status

Used by the Document Intelligence module.

Allowed values:

```text
SUCCESS
PARTIAL
FAILED
```

### Meaning

| Status | Meaning |
|---|---|
| `SUCCESS` | Processing completed successfully |
| `PARTIAL` | Some information was extracted, but processing was incomplete |
| `FAILED` | Processing could not be completed |

---

## 4.2 Verification Status

Used by Verification Providers.

Allowed values:

```text
VERIFIED
NOT_FOUND
INVALID
PENDING
ERROR
```

### Meaning

| Status | Meaning |
|---|---|
| `VERIFIED` | Information was successfully verified |
| `NOT_FOUND` | Identifier was checked but no matching record was found |
| `INVALID` | Identifier or submitted information is invalid |
| `PENDING` | Verification requires additional processing or is not yet complete |
| `ERROR` | Verification could not be completed because of a system or provider error |

---

## 4.3 Compliance Status

Reserved for the future Compliance Engine.

Allowed values:

```text
PASS
FAIL
REVIEW
PENDING
```

### Meaning

| Status | Meaning |
|---|---|
| `PASS` | Requirement is satisfied |
| `FAIL` | Requirement is not satisfied |
| `REVIEW` | Manual review is required |
| `PENDING` | Compliance cannot yet be determined |

Verification providers must NOT return `PASS` or `FAIL`.

Those statuses belong to the Compliance Engine.

---

## 4.4 Final Procurement Decision

Reserved for the Procurement Officer.

Allowed values:

```text
QUALIFIED
DISQUALIFIED
MANUAL_REVIEW
```

The AI system or verification provider must not make the final procurement decision.

---

# 5. Standard Document Processing Contract

Every document-processing operation must return a predictable structure.

The standard output format is:

```python
{
    "success": True,

    "processing_status": "SUCCESS",

    "document_type": "GST_CERTIFICATE",

    "extracted_data": {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd"
    },

    "confidence": 0.95,

    "errors": []
}
```

---

## 5.1 Field Definitions

### `success`

Indicates whether the processing module itself executed successfully.

Allowed values:

```python
True
False
```

Example:

```python
"success": True
```

means the module successfully processed the document.

---

### `processing_status`

Indicates the result of the document-processing operation.

Allowed values:

```text
SUCCESS
PARTIAL
FAILED
```

---

### `document_type`

Indicates the detected document type.

Example:

```python
"document_type": "GST_CERTIFICATE"
```

If the document type cannot be identified:

```python
"document_type": "UNKNOWN"
```

If processing completely fails:

```python
"document_type": None
```

---

### `extracted_data`

Contains the actual information extracted from the document.

Example:

```python
"extracted_data": {
    "gstin": "27ABCDE1234F1Z5",
    "legal_name": "ABC Industries Pvt Ltd"
}
```

If no data can be extracted:

```python
"extracted_data": {}
```

---

### `confidence`

Represents confidence in extraction or classification.

Range:

```text
0.0 to 1.0
```

Example:

```python
"confidence": 0.95
```

means approximately 95% confidence.

---

### `errors`

Contains a list of errors encountered.

Example:

```python
"errors": []
```

If errors occur:

```python
"errors": [
    "Unable to extract readable text from document"
]
```

---

# 6. Document Processing Examples

## 6.1 Successful Processing

```python
{
    "success": True,

    "processing_status": "SUCCESS",

    "document_type": "GST_CERTIFICATE",

    "extracted_data": {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd"
    },

    "confidence": 0.95,

    "errors": []
}
```

---

## 6.2 Partial Processing

Example: the document type was identified, but some fields could not be extracted.

```python
{
    "success": True,

    "processing_status": "PARTIAL",

    "document_type": "GST_CERTIFICATE",

    "extracted_data": {
        "gstin": "27ABCDE1234F1Z5"
    },

    "confidence": 0.70,

    "errors": [
        "Legal name could not be extracted"
    ]
}
```

---

## 6.3 Failed Processing

```python
{
    "success": False,

    "processing_status": "FAILED",

    "document_type": None,

    "extracted_data": {},

    "confidence": 0.0,

    "errors": [
        "Unable to extract readable text from document"
    ]
}
```

---

# 7. Initial Supported Document Types

The platform may eventually support many document types.

For the initial implementation, use:

```text
GST_CERTIFICATE
PAN_DOCUMENT
UDYAM_CERTIFICATE
OEM_AUTHORIZATION
UNKNOWN
```

Future document types may include:

```text
EPFO_DOCUMENT
ESIC_DOCUMENT
STARTUP_CERTIFICATE
NSIC_CERTIFICATE
LOCAL_CONTENT_DECLARATION
DIGILOCKER_DOCUMENT
OTHER
```

---

# 8. Standard Verification Provider Contract

Every verification provider must return a predictable structure.

The provider answers:

> Was this identifier or information successfully verified?

Standard output:

```python
{
    "success": True,

    "provider": "GST",

    "identifier": "27ABCDE1234F1Z5",

    "verification_status": "VERIFIED",

    "data": {
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_status": "ACTIVE"
    },

    "message": "GST registration verified successfully",

    "errors": []
}
```

---

# 9. Verification Output Field Definitions

## 9.1 `success`

Indicates whether the verification provider successfully executed.

Example:

```python
"success": True
```

means:

```text
The provider successfully performed the verification attempt.
```

It does NOT necessarily mean the identifier is valid.

---

## 9.2 `provider`

The name of the verification provider.

Example:

```python
"provider": "GST"
```

Allowed initial values:

```text
GST
PAN
UDYAM
```

Future providers:

```text
EPFO
ESIC
STARTUP_INDIA
NSIC
DEBARMENT
```

---

## 9.3 `identifier`

The value submitted for verification.

Example:

```python
"identifier": "27ABCDE1234F1Z5"
```

For GST:

```text
GSTIN
```

For PAN:

```text
PAN
```

For Udyam:

```text
Udyam Registration Number
```

---

## 9.4 `verification_status`

Allowed values:

```text
VERIFIED
NOT_FOUND
INVALID
PENDING
ERROR
```

This represents the actual result of verification.

---

## 9.5 `data`

Contains information returned by the verification source.

Example:

```python
"data": {
    "legal_name": "ABC Industries Pvt Ltd",
    "registration_status": "ACTIVE"
}
```

If no record exists:

```python
"data": {}
```

---

## 9.6 `message`

A short human-readable description.

Example:

```python
"message": "GST registration verified successfully"
```

---

## 9.7 `errors`

Contains system or provider errors.

Example:

```python
"errors": []
```

If a provider fails:

```python
"errors": [
    "Provider connection failed"
]
```

---

# 10. Verification Examples

## 10.1 Successfully Verified

```python
{
    "success": True,

    "provider": "GST",

    "identifier": "27ABCDE1234F1Z5",

    "verification_status": "VERIFIED",

    "data": {
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_status": "ACTIVE"
    },

    "message": "GST registration verified successfully",

    "errors": []
}
```

---

## 10.2 Record Not Found

```python
{
    "success": True,

    "provider": "GST",

    "identifier": "INVALID123",

    "verification_status": "NOT_FOUND",

    "data": {},

    "message": "No matching GST registration found",

    "errors": []
}
```

Important:

```text
success = True
```

because the provider itself worked correctly.

The result was simply:

```text
NOT_FOUND
```

---

## 10.3 Invalid Identifier

```python
{
    "success": True,

    "provider": "GST",

    "identifier": "INVALID-GST",

    "verification_status": "INVALID",

    "data": {},

    "message": "Invalid GSTIN format",

    "errors": []
}
```

---

## 10.4 Provider Error

```python
{
    "success": False,

    "provider": "GST",

    "identifier": "27ABCDE1234F1Z5",

    "verification_status": "ERROR",

    "data": {},

    "message": "Verification could not be completed",

    "errors": [
        "Provider connection failed"
    ]
}
```

---

# 11. Important Difference Between `success` and Status

These two fields have different purposes.

## Example 1: GST verified

```text
success = True
verification_status = VERIFIED
```

Meaning:

```text
The provider worked successfully.
The GST was successfully verified.
```

---

## Example 2: GST not found

```text
success = True
verification_status = NOT_FOUND
```

Meaning:

```text
The provider worked successfully.
The GST record was not found.
```

---

## Example 3: Provider failed

```text
success = False
verification_status = ERROR
```

Meaning:

```text
The verification provider itself failed.
The system could not determine the GST status.
```

This distinction must be maintained throughout the project.

---

# 12. Identifier Naming Standard

The following field names must be used consistently.

| Verification Type | Standard Field Name |
|---|---|
| GST | `gstin` |
| PAN | `pan` |
| Udyam | `udyam_number` |
| EPFO | `epfo_number` |
| ESIC | `esic_number` |

Do NOT use random alternatives such as:

```text
gst_no
gst_number
gst_id
gst_registration
pan_number
udyam_id
```

Use the defined standard.

---

# 13. Document to Verification Integration

The modules should integrate in the following way.

## Step 1 — Document Intelligence

Input:

```text
GST Certificate.pdf
```

Document Intelligence returns:

```python
{
    "success": True,

    "processing_status": "SUCCESS",

    "document_type": "GST_CERTIFICATE",

    "extracted_data": {
        "gstin": "27ABCDE1234F1Z5",
        "legal_name": "ABC Industries Pvt Ltd"
    },

    "confidence": 0.95,

    "errors": []
}
```

---

## Step 2 — Core Backend

The Core Backend reads:

```python
gstin = result["extracted_data"]["gstin"]
```

The Core Backend then calls:

```python
gst_result = verify_gst(gstin)
```

---

## Step 3 — Verification Provider

The Verification Provider returns:

```python
{
    "success": True,

    "provider": "GST",

    "identifier": "27ABCDE1234F1Z5",

    "verification_status": "VERIFIED",

    "data": {
        "legal_name": "ABC Industries Pvt Ltd",
        "registration_status": "ACTIVE"
    },

    "message": "GST registration verified successfully",

    "errors": []
}
```

---

## Step 4 — Future Cross-Verification

The future Cross-Verification Engine will compare:

```text
Bidder Submitted Information
           │
           ▼
Document Extracted Information
           │
           ▼
Provider Verification Information
```

Example:

```text
Submitted GSTIN:
27ABCDE1234F1Z5

Extracted GSTIN:
27ABCDE1234F1Z5

Verified GSTIN:
27ABCDE1234F1Z5

Result:
MATCH
```

---

# 14. Module Boundaries

## Core Backend

Owns:

```text
backend/app/main.py
backend/app/core/
backend/app/database/
backend/app/models/
backend/app/schemas/
backend/app/api/
backend/app/repositories/
```

Other team members should not modify these folders without coordination.

---

## Document Intelligence

Owns:

```text
backend/app/services/document_processing/
```

The Document Intelligence team should primarily work inside this directory.

They should not modify:

```text
main.py
core/
database/
models/
api/
```

without coordination.

---

## Verification Providers

Owns:

```text
backend/app/providers/
```

The Verification Provider team should primarily work inside this directory.

They should not modify:

```text
main.py
core/
database/
models/
api/
```

without coordination.

---

# 15. Folder Ownership Structure

```text
bidsure-ai/
│
├── docs/
│   └── module_contracts.md
│
├── backend/
│   │
│   ├── requirements.txt
│   │
│   ├── app/
│   │   │
│   │   ├── main.py                     ← Core Backend
│   │   │
│   │   ├── core/                       ← Core Backend
│   │   ├── database/                   ← Core Backend
│   │   ├── models/                     ← Core Backend
│   │   ├── schemas/                    ← Core Backend
│   │   ├── api/                        ← Core Backend
│   │   ├── repositories/               ← Core Backend
│   │   │
│   │   ├── services/
│   │   │   └── document_processing/    ← Document Intelligence
│   │   │
│   │   └── providers/                  ← Verification Providers
│   │
│   ├── tests/
│   │
│   └── experiments/
│
├── frontend/
│
└── mock_data/
```

---

# 16. Git Workflow

Nobody should directly push to the `main` branch.

Recommended branch structure:

```text
main
│
└── develop
    │
    ├── feature/core-backend
    │
    ├── feature/document-intelligence
    │
    └── feature/verification-providers
```

## Workflow

```text
develop
   │
   ▼
Create Feature Branch
   │
   ▼
Write Code
   │
   ▼
Test Locally
   │
   ▼
Commit Changes
   │
   ▼
Push Branch
   │
   ▼
Create Pull Request
   │
   ▼
Review
   │
   ▼
Merge into develop
```

No feature branch should directly merge itself into `main`.

---

# 17. Branch Naming Convention

Use:

```text
feature/<module-name>
```

Examples:

```text
feature/core-backend
feature/document-intelligence
feature/verification-providers
```

For bug fixes:

```text
fix/<issue-name>
```

Example:

```text
fix/gst-provider-validation
```

---

# 18. Python Coding Standards

## Variables and Functions

Use:

```python
snake_case
```

Examples:

```python
gstin
verify_gst()
extract_text()
process_document()
```

---

## Classes

Use:

```python
PascalCase
```

Examples:

```python
GSTProvider
DocumentProcessor
VerificationResult
```

---

## Constants

Use:

```python
UPPER_CASE
```

Examples:

```python
MAX_FILE_SIZE
SUPPORTED_DOCUMENT_TYPES
```

---

# 19. Type Hints

Use type hints wherever practical.

Example:

```python
def verify_gst(gstin: str) -> dict:
    ...
```

Example:

```python
def extract_text(file_path: str) -> str:
    ...
```

---

# 20. Function Design Rules

Prefer small functions with one responsibility.

Good:

```python
extract_text()
perform_ocr()
detect_document_type()
extract_gstin()
verify_gst()
```

Avoid:

```python
process_everything_and_verify_and_score()
```

A function should ideally have one clear responsibility.

---

# 21. Error Handling Rules

Modules should not silently fail.

Bad:

```python
try:
    ...
except Exception:
    pass
```

Better:

```python
try:
    ...
except Exception as error:
    return {
        "success": False,
        "errors": [str(error)]
    }
```

Errors should be returned using the module's standard output structure where appropriate.

---

# 22. Dependency Rules

A module should not depend on another unfinished module.

## Document Intelligence

The following should work independently:

```python
process_document("sample.pdf")
```

without requiring:

```text
Database
FastAPI
Frontend
Verification Providers
```

---

## Verification Providers

The following should work independently:

```python
verify_gst("27ABCDE1234F1Z5")
```

without requiring:

```text
Database
FastAPI
Frontend
Document Intelligence
```

---

# 23. Initial Development Targets

## Core Backend

Current development sequence:

```text
Phase 1.1
FastAPI Foundation
        ↓
Phase 1.2
Configuration Management
        ↓
Phase 1.3
Database Foundation
        ↓
Phase 1.4
Core Database Models
```

---

## Document Intelligence

Initial sequence:

```text
PDF File
   │
   ▼
PDF Text Extraction
   │
   ▼
Return Extracted Text
   │
   ▼
Document Classification
   │
   ▼
Field Extraction
   │
   ▼
Structured Output
```

Start with:

```text
PDF text extraction
GST document field extraction
PAN document field extraction
Udyam document field extraction
```

OCR can be added after basic PDF extraction works.

---

## Verification Providers

Initial sequence:

```text
Common Provider Interface
        │
        ▼
Mock Data
        │
        ▼
GST Provider
        │
        ▼
PAN Provider
        │
        ▼
Udyam Provider
```

Real government integrations can be considered later.

The provider architecture should allow:

```text
Mock Provider
       ↓
Later Replace With
       ↓
Official / Authorized Provider Integration
```

without changing the rest of the application.

---

# 24. Current Team Integration Architecture

```text
                         ┌─────────────────────┐
                         │    CORE BACKEND     │
                         │        YOU          │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  │                                   │
                  ▼                                   ▼
       ┌───────────────────────┐          ┌───────────────────────┐
       │ DOCUMENT INTELLIGENCE │          │ VERIFICATION PROVIDERS│
       │       PERSON 2        │          │       PERSON 3        │
       └───────────┬───────────┘          └───────────┬───────────┘
                   │                                  │
                   └───────────────┬──────────────────┘
                                   │
                                   ▼
                          FUTURE INTEGRATION
                                   │
                                   ▼
                         CROSS-VERIFICATION
                                   │
                                   ▼
                          COMPLIANCE ENGINE
                                   │
                                   ▼
                         SCORING & RISK ENGINE
                                   │
                                   ▼
                          AI RECOMMENDATION
                                   │
                                   ▼
                         PROCUREMENT OFFICER
                           FINAL DECISION
```

---

# 25. Final Rule

Every team member should follow this principle:

> Build your module so that it can be tested independently and integrated through a clearly defined input/output contract.

The responsibility of each module should remain separate:

```text
DOCUMENT INTELLIGENCE
"What information is inside this document?"
            │
            ▼
VERIFICATION PROVIDERS
"Is this information valid according to the source?"
            │
            ▼
CROSS-VERIFICATION
"Do the different sources match?"
            │
            ▼
COMPLIANCE ENGINE
"Does the bidder satisfy the tender requirement?"
            │
            ▼
SCORING ENGINE
"What is the overall compliance and risk level?"
            │
            ▼
AI RECOMMENDATION
"What should the Procurement Officer review?"
            │
            ▼
PROCUREMENT OFFICER
"Final qualification or disqualification decision"
```

This separation must be maintained throughout the development of BidSure AI.