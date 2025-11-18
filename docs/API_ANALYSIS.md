# Frontend and Backend API Analysis

## Overview
This document analyzes the alignment between the frontend API client (`src/api/client.ts`) and the backend API endpoints.

## Base Configuration

### Frontend
- **Base URL**: `VITE_API_URL` or defaults to `http://localhost:8000`
- **API Prefix**: `/api`
- **Auth**: JWT token stored in `localStorage.getItem('access_token')`
- **Headers**: `Authorization: Bearer {token}`

### Backend
- **Routers**: All mounted under `/api` prefix in `main.py`
- **Auth**: OAuth2 JWT token validation via `get_current_user` dependency
- **CORS**: Configured to allow frontend origins

## Endpoint Comparison

### ✅ Authentication (`/api/auth`)

| Frontend Method | Frontend Endpoint | Backend Endpoint | Status |
|----------------|-------------------|------------------|--------|
| `authAPI.login` | `POST /api/auth/token` | `POST /api/auth/token` | ✅ Match |
| `authAPI.register` | `POST /api/auth/register` | `POST /api/auth/register` | ✅ Match |
| `authAPI.getMe` | `GET /api/auth/me` | `GET /api/auth/me` | ✅ Match |

### ✅ CV Management (`/api/cv`)

| Frontend Method | Frontend Endpoint | Backend Endpoint | Status |
|----------------|-------------------|------------------|--------|
| `cvAPI.upload` | `POST /api/cv/upload` | `POST /api/cv/upload` | ✅ Match |
| `cvAPI.getProfile` | `GET /api/cv/profile` | `GET /api/cv/profile` | ✅ Match |
| `cvAPI.saveProfile` | `POST /api/cv/profile/save` | `POST /api/cv/profile/save` | ✅ Match |
| `cvAPI.deleteProfile` | `DELETE /api/cv/profile` | `DELETE /api/cv/profile` | ✅ Match |

### ✅ Jobs (`/api/jobs`)

| Frontend Method | Frontend Endpoint | Backend Endpoint | Status |
|----------------|-------------------|------------------|--------|
| `jobsAPI.search` | `GET /api/jobs` | `GET /api/jobs` | ✅ Match |
| `jobsAPI.searchVector` | `POST /api/jobs/search-vector` | `POST /api/jobs/search-vector` | ✅ Match |
| `jobsAPI.getById` | `GET /api/jobs/{id}` | `GET /api/jobs/{job_id}` | ✅ Match |
| `jobsAPI.getRecommended` | `GET /api/jobs/recommended` | `GET /api/jobs/recommended` | ✅ Match |
| `jobsAPI.getSimilar` | `GET /api/jobs/{jobId}/similar` | `GET /api/jobs/{job_id}/similar` | ✅ Match |

**Note**: Backend also has `POST /api/jobs/search` endpoint (not used by frontend currently)

### ✅ Matches (`/api/matches`)

| Frontend Method | Frontend Endpoint | Backend Endpoint | Status |
|----------------|-------------------|------------------|--------|
| `matchesAPI.getMatches` | `GET /api/matches` | `GET /api/matches` | ✅ Match |
| `matchesAPI.calculate` | `POST /api/matches/calculate` | `POST /api/matches/calculate` | ✅ Match |

### ✅ Applications (`/api/applications`)

| Frontend Method | Frontend Endpoint | Backend Endpoint | Status |
|----------------|-------------------|------------------|--------|
| `applicationsAPI.markApplied` | `POST /api/applications/mark-applied` | `POST /api/applications/mark-applied` | ✅ Match |
| `applicationsAPI.updateStatus` | `PUT /api/applications/{jobId}/status` | `PUT /api/applications/{job_id}/status` | ✅ Match |
| `applicationsAPI.getApplications` | `GET /api/applications/` | `GET /api/applications/` | ✅ Match |
| `applicationsAPI.checkStatus` | `GET /api/applications/status/{jobId}` | `GET /api/applications/status/{job_id}` | ✅ Match |
| `applicationsAPI.remove` | `DELETE /api/applications/{jobId}` | `DELETE /api/applications/{job_id}` | ✅ Match |
| `applicationsAPI.prepareInterview` | `POST /api/applications/{jobId}/prepare/interview` | `POST /api/applications/{job_id}/prepare/interview` | ✅ Match |
| `applicationsAPI.prepareCV` | `POST /api/applications/{jobId}/prepare/cv` | `POST /api/applications/{job_id}/prepare/cv` | ✅ Match |
| `applicationsAPI.refineCV` | `POST /api/applications/prepare/cv/{cvId}/refine` | `POST /api/applications/prepare/cv/{cv_id}/refine` | ✅ Match |
| `applicationsAPI.saveCVDraft` | `PUT /api/applications/prepare/cv/{cvId}/save` | `PUT /api/applications/prepare/cv/{cv_id}/save` | ✅ Match |
| `applicationsAPI.validateCV` | `POST /api/applications/prepare/cv/{cvId}/validate` | `POST /api/applications/prepare/cv/{cv_id}/validate` | ✅ Match |
| `applicationsAPI.exportCVToPDF` | `POST /api/applications/prepare/cv/{cvId}/export-pdf` | `POST /api/applications/prepare/cv/{cv_id}/export-pdf` | ✅ Match |
| `applicationsAPI.aiAssistCV` | `POST /api/applications/prepare/cv/{cvId}/assist` | `POST /api/applications/prepare/cv/{cv_id}/assist` | ✅ Match |
| `applicationsAPI.aiAssistCVStream` | `POST /api/applications/prepare/cv/{cvId}/assist/stream` | `POST /api/applications/prepare/cv/{cv_id}/assist/stream` | ✅ Match |
| `applicationsAPI.prepareCoverLetter` | `POST /api/applications/{jobId}/prepare/cover-letter` | `POST /api/applications/{job_id}/prepare/cover-letter` | ✅ Match |
| `applicationsAPI.getPreparationStatus` | `GET /api/applications/{jobId}/prepare/status` | `GET /api/applications/{job_id}/prepare/status` | ✅ Match |

**Additional Backend Endpoints** (not in frontend client):
- `GET /api/applications/prepare/cv/{cv_id}` - Get tailored CV
- `GET /api/applications/prepare/cv/{cv_id}/download` - Download CV (HTML/PDF)
- `GET /api/applications/prepare/cover-letter/{letter_id}` - Get cover letter
- `PUT /api/applications/prepare/cover-letter/{letter_id}` - Update cover letter

### ✅ Interview (`/api/interview`)

**Frontend Client**: `src/api/interviewClient.ts`

| Frontend Method | Frontend Endpoint | Backend Endpoint | Status |
|----------------|-------------------|------------------|--------|
| `interviewAPI.startSession` | `POST /api/interview/sessions/start` | `POST /api/interview/sessions/start` | ✅ Match |
| `interviewAPI.getNextQuestion` | `GET /api/interview/sessions/{sessionId}/next-question` | `GET /api/interview/sessions/{session_id}/next-question` | ✅ Match |
| `interviewAPI.submitAnswer` | `POST /api/interview/sessions/{sessionId}/submit-answer` | `POST /api/interview/sessions/{session_id}/submit-answer` | ✅ Match |
| `interviewAPI.getSessionHistory` | `GET /api/interview/sessions/history` | `GET /api/interview/sessions/history` | ✅ Match |
| `interviewAPI.getSessionsByJob` | `GET /api/interview/sessions/job/{jobId}` | `GET /api/interview/sessions/job/{job_id}` | ✅ Match |
| `interviewAPI.getSessionDetail` | `GET /api/interview/sessions/{sessionId}` | `GET /api/interview/sessions/{session_id}` | ✅ Match |
| `interviewAPI.getAnalytics` | `GET /api/interview/analytics` | `GET /api/interview/analytics` | ✅ Match |
| `interviewAPI.abandonSession` | `POST /api/interview/sessions/{sessionId}/abandon` | `POST /api/interview/sessions/{session_id}/abandon` | ✅ Match |
| `interviewAPI.getQuestions` | `GET /api/interview/questions` | `GET /api/interview/questions` | ✅ Match |

## Request/Response Format Analysis

### Authentication
- **Login**: Frontend sends `FormData` with `username` and `password` ✅
- **Register**: Frontend sends JSON `{username, password}` ✅
- **Response**: Both return `{access_token, token_type}` ✅

### CV Upload
- **Frontend**: Sends `FormData` with `file` field ✅
- **Backend**: Expects `UploadFile` ✅
- **Response**: Returns parsed CV data ✅

### Job Search Vector
- **Frontend**: Sends body with `query`, `limit`, `use_llm_enhancement`, `score_threshold` ✅
- **Frontend**: Sends query params: `location`, `hide_saved`, `limit`, `offset` ✅
- **Backend**: Accepts `JobDataSearch` model in body and query params ✅

### Applications
- **markApplied**: Frontend sends `{job_id, status, notes}` ✅
- **updateStatus**: Frontend sends `{status, notes}` ✅
- **exportCVToPDF**: Frontend sends optional `html_content` or `html_filename` in body ✅

## Error Handling

### Frontend
- **401 Errors**: Automatically redirects to `/login` and removes token ✅
- **Error Interceptor**: Logs errors and rejects promise ✅

### Backend
- **401 Errors**: Returns proper `WWW-Authenticate` header ✅
- **404 Errors**: Returns appropriate error messages ✅
- **500 Errors**: Returns error details (in development) ✅

## Potential Issues

### ⚠️ Minor Issues

1. **Missing Frontend Methods**:
   - `GET /api/applications/prepare/cv/{cv_id}` - Get tailored CV (may be used directly)
   - `GET /api/applications/prepare/cv/{cv_id}/download` - Download CV (may be used directly)
   - `GET /api/applications/prepare/cover-letter/{letter_id}` - Get cover letter
   - `PUT /api/applications/prepare/cover-letter/{letter_id}` - Update cover letter

2. **Unused Backend Endpoint**:
   - `POST /api/jobs/search` - Vector search endpoint (frontend uses `/search-vector` instead)

### ✅ Strengths

1. **Consistent Naming**: Parameter names match between frontend and backend (e.g., `job_id` vs `jobId` in URLs is handled correctly)
2. **Error Handling**: Both sides handle errors appropriately
3. **Auth Flow**: JWT token handling is consistent
4. **Type Safety**: Frontend has TypeScript interfaces, backend has Pydantic models

## Recommendations

1. **Add Missing Frontend Methods** (if needed):
   - Consider adding methods for getting/downloading tailored CVs and cover letters if they're accessed directly
   
2. **Documentation**:
   - All endpoints are well-documented in backend code
   - Frontend client has clear method names

3. **Testing**:
   - Consider adding integration tests to verify frontend-backend compatibility

## Summary

✅ **Overall Status**: Frontend and backend APIs are **well-aligned** with no critical mismatches.

- All frontend API calls have corresponding backend endpoints
- Request/response formats match
- Authentication flow is consistent
- Error handling is appropriate on both sides

The API integration appears to be **production-ready** with only minor optional enhancements possible.

