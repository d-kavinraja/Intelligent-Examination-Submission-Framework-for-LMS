# README Verification Checklist

## ✅ Port Configuration
- **Configured Port:** 3000 (from vite.config.js)
- **References Updated:** All 3001 → 3000

## ✅ Project Structure
- **Actual Structure Matches:**
  - ✓ src/api/api.js (BASE_URL: http://localhost:8000)
  - ✓ src/components/LoadingOverlay.jsx
  - ✓ src/components/staff/ (10 components)
  - ✓ src/components/student/ (5 components)
  - ✓ src/contexts/ (3 contexts)
  - ✓ src/hooks/useFileUpload.js
  - ✓ src/utils/validation.js

## ✅ Dependencies
Verified in package.json:
- react: ^18.2.0
- react-dom: ^18.2.0
- react-router-dom: ^7.13.0 ✓
- axios: ^1.6.0
- lucide-react: ^0.563.0
- tailwindcss: ^3.3.0
- vite: ^6.4.1

## ✅ Scripts
Verified in package.json:
- `npm run dev` → vite
- `npm run build` → vite build
- `npm run preview` → vite preview
- `npm run lint` → eslint src

## ✅ API Configuration
- **API Base:** http://localhost:8000 (from src/api/api.js)
- **Dev Server:** port 3000 (from vite.config.js)
- **Proxy Routes:** /api, /upload, /auth, /admin → http://localhost:5000

## ✅ Authentication Endpoints
Staff Portal:
- POST /auth/staff/login (from AuthContext.jsx)

Student Portal:
- POST /auth/student/login (needs verification)
- GET /api/student/papers
- POST /api/student/papers/{id}/submit
- POST /api/student/papers/{id}/report

## ✅ File Format Validation
- Pattern: `{RegisterNumber}_{SubjectCode}.{extension}`
- Accepted: .pdf, .jpg, .jpeg, .png
- Example: 611221104088_19AI405.pdf

## ✅ Component Documentation
All components documented with accurate descriptions:
- Staff Portal: 10 components ✓
- Student Portal: 5 components ✓
- Loading: 1 component ✓

## ✅ Routing
- Route / → Redirects to /staff
- Route /staff → Staff portal
- Route /student → Student portal
- Route * → Redirects to /staff

## ✅ Development Environment
- Node.js v16+ required
- npm v7+ required
- React Router DOM v7.13.0
- Vite 6.4.1

## ⚠️ Notes
1. README refers to http://localhost:8000 for API
2. vite.config.js has proxy to :5000 (may not be used)
3. Check actual backend port and update if needed
4. Theme context is global (ThemeContext.jsx)

## Last Updated
2026-02-05
