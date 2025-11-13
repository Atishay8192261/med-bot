# Backend Integration Guide for Indian Medicine Chatbot Frontend

## Overview
This document provides comprehensive instructions for backend developers to integrate with the Indian Medicine Chatbot frontend built with Next.js 14, TypeScript, and TailwindCSS.

## API Configuration Requirements

### Environment Variables
The frontend requires **one primary environment variable**:

\`\`\`bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
\`\`\`

**Important Notes:**
- This is the **only API key/configuration** needed
- Must be prefixed with `NEXT_PUBLIC_` to be accessible in the browser
- Default fallback is `http://localhost:8000` if not set
- For production, set this to your deployed backend URL (e.g., `https://api.yourdomain.com`)

### Setting Environment Variables

#### Local Development (.env.local)
\`\`\`bash
# Create .env.local in the project root
NEXT_PUBLIC_API_BASE=http://localhost:8000
\`\`\`

#### Production (Vercel/Deployment)
\`\`\`bash
# Set in your deployment platform
NEXT_PUBLIC_API_BASE=https://your-api-domain.com
\`\`\`

## Required API Endpoints

The frontend expects these **7 REST endpoints** from your backend:

### 1. Search Endpoint
\`\`\`http
GET /search?query={query}&limit={limit}
\`\`\`
**Response Type:** `SearchResponse`
\`\`\`typescript
{
  query: string;
  hits: ResolveItem[];
}
\`\`\`

### 2. Resolve Endpoint
\`\`\`http
GET /resolve?name={name}&limit={limit}
\`\`\`
**Response Type:** `ResolveItem[]` or `{items: ResolveItem[]}`

### 3. Monograph Endpoints
\`\`\`http
GET /monograph?signature={signature}
GET /monograph?name={name}
\`\`\`
**Response Type:** `MonographResponse`

### 4. Alternatives Endpoints
\`\`\`http
GET /alternatives?signature={signature}
GET /alternatives?name={name}
\`\`\`
**Response Type:** `AlternativesResponse`

### 5. Advise Endpoint
\`\`\`http
GET /advise?signature={signature}&name={name}&query={query}&intent={intent}&lang={lang}
\`\`\`
**Response Type:** `AdviseResponse`

### 6. Health Endpoint
\`\`\`http
GET /health
\`\`\`
**Response Type:** `HealthResponse`

## Complete TypeScript Data Contracts

Your backend must return JSON responses matching these **exact TypeScript interfaces**:

\`\`\`typescript
// Core Types
export interface ResolveItem {
  id?: number;
  brand_name: string;
  manufacturer?: string | null;
  mrp_inr?: number | null;
  salt_signature?: string | null;
  salts: string[];
}

export interface SearchResponse {
  query: string;
  hits: ResolveItem[];
}

// Monograph Types
export interface MonographSections {
  uses?: string[];
  how_to_take?: string[];
  precautions?: string[];
  side_effects?: string[];
}

export interface MonographResponse {
  title?: string;
  sections: MonographSections;
  sources?: { name: string; url: string }[];
  disclaimer: string;
}

// Alternatives Types
export interface AlternativesPriceSummary {
  min?: number | null;
  q1?: number | null;
  median?: number | null;
  q3?: number | null;
  max?: number | null;
  count?: number | null;
}

export interface AlternativeBrand {
  brand_name: string;
  manufacturer?: string | null;
  mrp_inr?: number | null;
  pack?: string | null;
  dosage_form?: string | null;
  salt_signature?: string | null;
  sources?: string[]; // ["catalog", "janaushadhi", "nppa"]
}

export interface AlternativesResponse {
  brands: AlternativeBrand[];
  janaushadhi?: AlternativeBrand[];
  nppa_ceiling_price?: number | null;
  price_summary?: AlternativesPriceSummary;
  disclaimer: string;
}

// Advise Types
export interface AdviseResponse {
  intent: string;
  signature?: string | null;
  salts: string[];
  answer: string;
  sources?: { name: string; url: string }[];
  alternatives?: AlternativesResponse;
  disclaimer: string;
}

// Health Types
export interface HealthResponse {
  ok: boolean;
  db: boolean;
  db_error?: string | null;
  search_backend: "os" | "pg";
  search_ok: boolean;
  external?: Record<string, "ok" | "fail">;
}
\`\`\`

## VS Code Development Setup

### 1. Clone and Setup Frontend
\`\`\`bash
# Clone the frontend repository
git clone <frontend-repo-url>
cd indian-medicine-chatbot

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_BASE=http://localhost:8000" > .env.local

# Start development server
npm run dev
\`\`\`

### 2. Backend Development Workflow

#### Option A: Separate Repositories
\`\`\`bash
# Terminal 1: Backend
cd /path/to/your-backend
python manage.py runserver 8000  # Django
# OR
npm start  # Node.js/Express
# OR
go run main.go  # Go

# Terminal 2: Frontend
cd /path/to/frontend
npm run dev
\`\`\`

#### Option B: Monorepo Structure
\`\`\`
project-root/
├── backend/          # Your API server
├── frontend/         # This Next.js app
├── shared/           # Shared types/utilities
└── docker-compose.yml
\`\`\`

### 3. VS Code Extensions Recommended
\`\`\`json
// .vscode/extensions.json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "ms-python.python",
    "ms-vscode.rest-client"
  ]
}
\`\`\`

### 4. API Testing with REST Client
Create `.vscode/api-tests.http`:
\`\`\`http
### Search Test
GET http://localhost:8000/search?query=augmentin&limit=8

### Resolve Test
GET http://localhost:8000/resolve?name=augmentin&limit=10

### Monograph Test
GET http://localhost:8000/monograph?signature=21216-723

### Alternatives Test
GET http://localhost:8000/alternatives?signature=21216-723

### Advise Test
GET http://localhost:8000/advise?signature=21216-723&query=side effects&lang=en

### Health Check
GET http://localhost:8000/health
\`\`\`

## CORS Configuration

Your backend **must** enable CORS for the frontend domain:

### Django (django-cors-headers)
\`\`\`python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Development
    "https://yourdomain.com", # Production
]

CORS_ALLOW_CREDENTIALS = True
\`\`\`

### Express.js
\`\`\`javascript
const cors = require('cors');
app.use(cors({
  origin: ['http://localhost:3000', 'https://yourdomain.com'],
  credentials: true
}));
\`\`\`

### FastAPI
\`\`\`python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
\`\`\`

## Frontend API Client Implementation

The frontend uses this API client (`lib/api-client.ts`):

\`\`\`typescript
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function getJSON<T>(path: string, params?: Record<string,string | number | boolean>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) Object.entries(params).forEach(([k,v]) => url.searchParams.set(k, String(v)));
  const r = await fetch(url.toString(), { cache: "no-store" });
  if (!r.ok) throw new Error(`GET ${url} -> ${r.status}`);
  return r.json() as Promise<T>;
}

export const api = {
  search: (query: string, limit = 10) => getJSON<SearchResponse>("/search", { query, limit }),
  resolve: (name: string, limit = 10) => getJSON<ResolveItem[] | {items: ResolveItem[]}>("/resolve", { name, limit }),
  monographBySignature: (signature: string) => getJSON<MonographResponse>("/monograph", { signature }),
  monographByName: (name: string) => getJSON<MonographResponse>("/monograph", { name }),
  alternativesBySignature: (signature: string) => getJSON<AlternativesResponse>("/alternatives", { signature }),
  alternativesByName: (name: string) => getJSON<AlternativesResponse>("/alternatives", { name }),
  advise: (opts: { signature?: string; name?: string; query?: string; intent?: string; lang?: "en" | "hi" }) =>
    getJSON<AdviseResponse>("/advise", opts as any),
  health: () => getJSON<HealthResponse>("/health")
};
\`\`\`

## Error Handling Requirements

Your API should return proper HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (drug/signature not found)
- **500**: Internal Server Error

Error response format:
\`\`\`json
{
  "error": "Drug not found",
  "code": "DRUG_NOT_FOUND",
  "details": "No drug found with signature: invalid-signature"
}
\`\`\`

## Sample API Responses

### Search Response Example
\`\`\`json
{
  "query": "augmentin",
  "hits": [
    {
      "id": 1,
      "brand_name": "Augmentin 625 Duo Tablet",
      "manufacturer": "Glaxo SmithKline Pharmaceuticals Ltd",
      "mrp_inr": 204.5,
      "salt_signature": "21216-723",
      "salts": ["Amoxycillin", "Clavulanic Acid"]
    }
  ]
}
\`\`\`

### Monograph Response Example
\`\`\`json
{
  "title": "Augmentin 625 Duo Tablet",
  "sections": {
    "uses": [
      "Treatment of bacterial infections",
      "Respiratory tract infections"
    ],
    "how_to_take": [
      "Take with food to reduce stomach upset",
      "Complete the full course as prescribed"
    ],
    "precautions": [
      "Inform your doctor about allergies",
      "Avoid alcohol during treatment"
    ],
    "side_effects": [
      "Nausea and vomiting",
      "Diarrhea",
      "Skin rash"
    ]
  },
  "sources": [
    {
      "name": "DailyMed",
      "url": "https://dailymed.nlm.nih.gov/..."
    }
  ],
  "disclaimer": "This information is for educational purposes only..."
}
\`\`\`

## Deployment Integration

### Environment Variables for Production
\`\`\`bash
# Vercel
NEXT_PUBLIC_API_BASE=https://api.yourdomain.com

# Netlify
NEXT_PUBLIC_API_BASE=https://api.yourdomain.com

# Docker
ENV NEXT_PUBLIC_API_BASE=https://api.yourdomain.com
\`\`\`

### Docker Compose Example
\`\`\`yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE=http://backend:8000
    depends_on:
      - backend
\`\`\`

## Testing Integration

### 1. Backend API Tests
Ensure your endpoints return the exact TypeScript interfaces shown above.

### 2. Frontend Integration Tests
The frontend includes integration tests that mock your API responses.

### 3. End-to-End Testing
\`\`\`bash
# Start both servers
npm run dev          # Frontend on :3000
python manage.py runserver 8000  # Backend on :8000

# Test critical paths
# 1. Search "augmentin" → should show results
# 2. Click result → should navigate to /drug/[signature]
# 3. Check all 3 tabs load properly
# 4. Test /status page shows backend health
\`\`\`

## Troubleshooting Common Issues

### 1. CORS Errors
\`\`\`
Access to fetch at 'http://localhost:8000/search' from origin 'http://localhost:3000' has been blocked by CORS policy
\`\`\`
**Solution**: Configure CORS in your backend (see CORS section above)

### 2. API Base URL Issues
\`\`\`
TypeError: Failed to fetch
\`\`\`
**Solution**: Check `NEXT_PUBLIC_API_BASE` environment variable is set correctly

### 3. Type Mismatches
\`\`\`
Property 'brand_name' is missing in type
\`\`\`
**Solution**: Ensure your API responses match the TypeScript interfaces exactly

### 4. Network Errors
The frontend shows "Something went wrong" with retry buttons and links to `/status` page.

## Performance Considerations

### 1. API Response Times
- Search: < 200ms (with debouncing)
- Monograph: < 500ms
- Alternatives: < 1s
- Advise: < 3s (AI processing)

### 2. Caching Strategy
The frontend uses `cache: "no-store"` for real-time data. Consider implementing:
- Redis caching for frequently accessed drugs
- CDN caching for static monograph data
- Database query optimization

### 3. Rate Limiting
Implement rate limiting on your API:
- Search: 100 requests/minute per IP
- Advise: 10 requests/minute per IP (AI expensive)

## Security Considerations

### 1. Input Validation
Validate all query parameters:
- `query`: Max 100 characters, alphanumeric + spaces
- `signature`: Format validation (e.g., "21216-723")
- `limit`: Integer between 1-50

### 2. SQL Injection Prevention
Use parameterized queries for all database operations.

### 3. API Authentication (Future)
The current implementation doesn't require authentication, but you can add:
- API keys for rate limiting
- JWT tokens for user-specific features

## Monitoring and Logging

### 1. Health Endpoint Implementation
\`\`\`python
# Example Django view
def health_check(request):
    return JsonResponse({
        "ok": True,
        "db": check_database_connection(),
        "search_backend": "pg",
        "search_ok": check_search_service(),
        "external": {
            "dailymed": "ok",
            "openfda": "fail"
        }
    })
\`\`\`

### 2. Logging Requirements
Log these events for debugging:
- Search queries and result counts
- API response times
- Error rates by endpoint
- Popular drug signatures

## Next Steps

1. **Set up your backend** with the 7 required endpoints
2. **Configure CORS** for `http://localhost:3000`
3. **Test each endpoint** using the provided `.http` file
4. **Set environment variable** `NEXT_PUBLIC_API_BASE`
5. **Start both servers** and test the integration
6. **Deploy to production** with proper environment variables

## Support

If you encounter issues during integration:
1. Check the `/status` page for backend health
2. Use browser DevTools Network tab to inspect API calls
3. Verify API responses match the TypeScript interfaces
4. Test endpoints directly with curl or Postman

The frontend is fully implemented and ready for your backend integration!
