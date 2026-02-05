# Examination Middleware - React Portal Application

A modern, dual-portal React application for managing examination papers. Features separate portals for staff (file uploads) and students (paper submission) with role-based routing, dark mode support, and real-time updates.

**Live Portals:**
- **Staff Portal:** `http://localhost:3000/staff` - Upload and manage examination papers
- **Student Portal:** `http://localhost:3000/student` - Access and submit examination papers

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Building for Production](#building-for-production)
- [Key Features](#key-features)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Ensure you have the following installed on your system:

- **Node.js** v16 or higher ([Download](https://nodejs.org/))
- **npm** v7+ (comes with Node.js)
- **Git** (optional, for version control)

To verify installation:
```bash
node --version
npm --version
```

---

## Project Structure

```
react-app/
├── src/
│   ├── api/
│   │   └── api.js                          # API client (baseURL: http://localhost:8000)
│   ├── components/
│   │   ├── LoadingOverlay.jsx              # Loading spinner overlay
│   │   ├── staff/                          # Staff portal components
│   │   │   ├── Alert.jsx                   # Alert/notification component
│   │   │   ├── FileList.jsx                # Selected files list display
│   │   │   ├── LoginSection.jsx            # Staff login form
│   │   │   ├── Navbar.jsx                  # Staff navigation bar
│   │   │   ├── PreviousUploadsSection.jsx  # Previously uploaded files table
│   │   │   ├── StatsSection.jsx            # Statistics cards
│   │   │   ├── UploadPortal.jsx            # Main staff portal container
│   │   │   ├── UploadResults.jsx           # Upload result modal
│   │   │   ├── UploadSection.jsx           # Upload button & progress bar
│   │   │   └── UploadZone.jsx              # Drag & drop upload area
│   │   └── student/                        # Student portal components
│   │       ├── PaperCard.jsx               # Individual paper card
│   │       ├── StudentLoginSection.jsx     # Student login form
│   │       ├── StudentNavbar.jsx           # Student navigation bar
│   │       ├── StudentPortal.jsx           # Main student portal container
│   │       └── StudentWelcomeBanner.jsx    # Welcome section with stats
│   ├── contexts/
│   │   ├── AuthContext.jsx                 # Staff authentication state
│   │   ├── StudentAuthContext.jsx          # Student authentication state
│   │   └── ThemeContext.jsx                # Theme toggle state (dark/light)
│   ├── hooks/
│   │   └── useFileUpload.js                # File upload state management
│   ├── utils/
│   │   └── validation.js                   # Filename validation logic
│   ├── App.jsx                             # Main app with React Router setup
│   ├── index.css                           # Tailwind & global styles
│   └── main.jsx                            # React entry point + BrowserRouter
├── index.html                              # HTML template
├── vite.config.js                          # Vite config (port: 3000)
├── tailwind.config.js                      # Tailwind customization
├── postcss.config.js                       # PostCSS setup
├── package.json                            # Dependencies & scripts
├── package-lock.json                       # Locked versions
└── README.md                               # Documentation
```

---

## Installation & Setup

### 1. Clone/Download the Project

```bash
cd d:\lms-paper\react-app
# or your project directory
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages:
- **react** - UI library
- **react-dom** - React DOM binding
- **react-router-dom** - Client-side routing (for /staff and /student routes)
- **axios** - HTTP client for API calls
- **lucide-react** - Icon library
- **tailwindcss** - Utility-first CSS framework
- **vite** - Build tool and dev server

---

## Running the Application

### Development Mode

Start the development server with hot module reloading:

```bash
npm run dev
```

Output:
```
  VITE v6.4.1  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

The app will automatically open at `http://localhost:3000/` and reload on code changes.

### Access the Portals

- **Root URL:** `http://localhost:3000/` → Redirects to `/staff`
- **Staff Portal:** `http://localhost:3000/staff` - Upload & manage exam papers
- **Student Portal:** `http://localhost:3000/student` - View & submit papers

---

## Building for Production

### Create an Optimized Build

```bash
npm run build
```

This generates a production-ready bundle in the `dist/` folder with:
- Minified JavaScript
- Optimized CSS
- Source maps (for debugging)
- Gzip compression support

### Preview the Build Locally

```bash
npm run preview
```

This starts a local preview server showing the production build.

---

## Key Features

### 🔀 Dual Portal Architecture
- **Staff Portal** (`/staff`): Upload examination papers with drag-and-drop
- **Student Portal** (`/student`): Access and submit exam papers
- **URL-based routing** - Clean, bookmarkable URLs for each portal

### 🎨 Modern UI/UX
- Tailwind CSS for responsive design
- Dark/Light mode toggle
- Smooth animations and transitions
- Mobile-friendly layout
- Professional color scheme

### 🔐 Authentication
- **Staff Login:** Username + Password
- **Student Login:** Username + Password + Register Number
- Token-based session management
- Persistent login (localStorage)

### 📁 File Management
- **Drag & drop** file upload
- **Filename validation** (format: `{RegisterNumber}_{SubjectCode}.{pdf|jpg|jpeg|png}`)
- **Visual feedback** for valid/invalid files
- **Bulk upload** support
- **Progress tracking** with percentage

### 📊 Real-time Monitoring
- Live statistics for uploads
- Paper status tracking (Pending/Submitted)
- Automatic polling for updates
- Report management for discrepancies

### 🌓 Theme Support
- Dark mode for comfortable viewing
- Persistent theme preference
- System theme detection

---

## Configuration

### API Configuration

The app connects to a backend API. The base URL is configured in [src/api/api.js](src/api/api.js):

```javascript
const BASE_URL = "http://localhost:8000"
```

Update this value if your backend runs on a different host/port.

### Vite Development Server

The development server is configured in [vite.config.js](vite.config.js):

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': 'http://localhost:5000',
    '/upload': 'http://localhost:5000',
    '/auth': 'http://localhost:5000',
    '/admin': 'http://localhost:5000',
  }
}
```

- **Dev Server Port:** 3000
- **API Endpoint:** http://localhost:8000
- **Proxy Routes:** Available if your backend uses different ports

### Tailwind Customization

Edit [tailwind.config.js](tailwind.config.js) to customize:
- Color scheme (primary, secondary colors)
- Typography (fonts, sizes)
- Spacing and breakpoints

---

## Common Tasks

### Login to Staff Portal

1. Navigate to `http://localhost:3000/staff`
2. Enter credentials:
   - **Username:** Staff username
   - **Password:** Staff password
3. Click "Login"
4. Upload exam papers using drag-and-drop or file browser

**File Format for Upload:**
```
{RegisterNumber}_{SubjectCode}.{extension}
```
**Example:** `611221104088_19AI405.pdf`
**Accepted Formats:** `.pdf`, `.jpg`, `.jpeg`, `.png`

### Login to Student Portal

1. Navigate to `http://localhost:3000/student`
2. Enter credentials:
   - **Moodle Username:** Your Moodle account username
   - **Moodle Password:** Your Moodle account password
   - **Register Number:** Your 12-digit university register number
3. Click "Sign In"
4. View assigned papers in the grid layout
5. Use action buttons to View, Submit, or Report papers

### Enable Dark Mode

Click the theme toggle button in the navbar (usually in top-right corner).

---

## Troubleshooting

### Port 3000 Already in Use

If port 3000 is in use, Vite will automatically try the next available port:

```bash
npm run dev
# Output will show: ➜  Local:   http://localhost:3001/ (or 3002, etc.)
```

To specify a custom port:
```bash
npm run dev -- --port 3005
```

**Note:** Default port is configured to 3000 in [vite.config.js](vite.config.js).

### Dependencies Installation Failed

Clear npm cache and reinstall:

```bash
npm cache clean --force
rm -r node_modules package-lock.json
npm install
```

### API Connection Errors

Verify the backend API is running and accessible:

```bash
curl http://localhost:8000/api/health
```

Update the API URL in [src/api/api.js](src/api/api.js) if the backend runs on a different host/port.

### Hot Module Reloading Not Working

Restart the dev server:

```bash
# Stop: Ctrl + C
npm run dev
```

### CSS Not Loading Properly

Clear browser cache:
- Press `Ctrl + Shift + Delete` (or `Cmd + Shift + Delete` on Mac)
- Clear cache and cookies
- Reload the page

---

## Development Tips

### Code Structure

- **Components** are organized by portal (staff/student)
- **Contexts** manage global state (auth, theme)
- **Hooks** encapsulate reusable logic
- **Utils** contain helper functions

### Adding New Routes

Edit [App.jsx](src/App.jsx) to add new routes:

```jsx
<Route path="/new-page" element={<YourComponent />} />
```

### Styling Guidelines

- Use Tailwind utility classes for styling
- Avoid inline styles unless dynamic
- Reference color scheme from [tailwind.config.js](tailwind.config.js)

### Debugging

- Open browser DevTools: `F12` or `Ctrl + Shift + I`
- Check Console tab for errors
- Use React DevTools extension for component inspection

---

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint (if configured) |

---

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

---

## Additional Resources

- [React Documentation](https://react.dev)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Vite Documentation](https://vitejs.dev)
- [React Router Docs](https://reactrouter.com)

---

## Support & Contributions

For issues or feature requests, please contact the development team.

---

## Staff Portal Components

### LoginSection
Handles staff authentication with username and password. Validates credentials and stores authentication token.

### UploadPortal
Main component combining all staff portal features. Manages file selection, upload state, and results display.

### Navbar
Displays user information, stats summary, and logout button with dark mode toggle.

### UploadZone
Drag-and-drop area for file selection. Click to browse files or drag files onto the area.

### FileList
Lists all selected files with validation status indicators (valid/invalid). Easy file removal with delete button.

### UploadSection
Controls for uploading files. Shows upload button, progress bar, and clear selection button.

### UploadResults
Modal displaying upload results for each file with success/error status and detailed messages.

### PreviousUploadsSection
Table of previously uploaded files with:
- Real-time search/filter
- Status badges (Uploaded, Processing, etc.)
- Action buttons (View, Reports, etc.)
- Pagination support

### StatsSection
4 stat cards showing:
- Total Files
- Valid Files
- Invalid Files
- Successfully Uploaded Files

### Alert
Reusable alert component with different types (info, warning, error, success).

---

## Student Portal Components

### StudentLoginSection
Student authentication form with fields for:
- Moodle Username
- Moodle Password
- 12-digit Register Number
- Security information display

### StudentPortal
Main student portal component. Displays assigned examination papers in a grid layout.

### StudentNavbar
Navigation bar with:
- Student name display
- Poll interval controls (for real-time updates)
- Report count badge
- Dark mode toggle
- Logout button

### StudentWelcomeBanner
Welcome section showing:
- Student greeting
- Statistics (Total Papers, Pending, Submitted)

### PaperCard
Individual paper display card showing:
- Subject code and register number
- File information and upload date
- Status badge (Pending/Submitted)
- Action buttons (View, Submit, Report)

---

## API Integration

The app expects the following backend endpoints:

### Staff Portal
- `POST /auth/staff/login` - Staff authentication
- `POST /upload/bulk` - Bulk file upload
- `GET /upload/all` - Get uploaded files list
- `GET /upload/stats` - Get upload statistics

### Student Portal
- `POST /auth/student/login` - Student authentication
- `GET /api/student/papers` - Get assigned papers
- `POST /api/student/papers/{id}/submit` - Submit a paper
- `POST /api/student/papers/{id}/report` - Report a paper issue

All requests include the `Authorization: Bearer {token}` header.

---

## Customization Guide

### Changing Colors

Edit [tailwind.config.js](tailwind.config.js):

```javascript
theme: {
  extend: {
    colors: {
      'primary': {
        600: '#2563eb',    // Change primary blue
        700: '#1d4ed8',
      },
      'emerald': {         // Student portal green
        600: '#10b981',
      }
    }
  }
}
```

### Modifying Authentication

Edit the respective auth context files:
- Staff: [src/contexts/AuthContext.jsx](src/contexts/AuthContext.jsx)
- Student: [src/contexts/StudentAuthContext.jsx](src/contexts/StudentAuthContext.jsx)

### Adding New Pages

1. Create component in `src/components/`
2. Add route in [App.jsx](src/App.jsx):
   ```jsx
   <Route path="/new-page" element={<NewComponent />} />
   ```

### Styling New Components

Use Tailwind utility classes:
```jsx
<div className="bg-white dark:bg-gray-900 rounded-lg p-4 shadow-md">
  {/* Content */}
</div>
```

---

## Dependency Management

### Update Dependencies

```bash
npm outdated                    # Check for outdated packages
npm update                      # Update to latest compatible versions
npm install package@latest      # Update specific package
```

### Lock File

The `package-lock.json` file locks all dependency versions. Commit this file to version control for reproducible installations.

---

## Performance Optimization Tips

1. **Lazy Load Components:** Use React.lazy() for code splitting
2. **Optimize Images:** Compress and use WebP format
3. **Debounce Search:** Add debouncing to real-time search
4. **Memoize Components:** Use React.memo() for expensive renders
5. **Monitor Bundle Size:** Use `npm run build` and check dist/ folder

---

## Security Considerations

1. **Token Storage:** Tokens stored in localStorage (consider sessionStorage for higher security)
2. **HTTPS:** Always use HTTPS in production
3. **CORS:** Configure backend CORS for trusted domains only
4. **Input Validation:** Validate filenames and user inputs
5. **Rate Limiting:** Implement API rate limiting on backend

---

## Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Other Platforms

1. Run `npm run build`
2. Upload `dist/` folder to your hosting
3. Configure server to serve `index.html` for all routes (for React Router)

### Environment Setup for Production

Create `.env.production`:
```
VITE_API_BASE_URL=https://api.yourdomain.com
```

---

## License

Educational use - Saveetha Engineering College

---

## Version History

- **v1.0.0** (Current) - Initial release with dual portals and routing
