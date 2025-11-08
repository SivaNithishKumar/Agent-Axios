# Authentication Integration Guide

## Overview
This guide documents the authentication system integration for the CVE Analyzer frontend application. The implementation includes a complete authentication flow with login, registration, token management, and protected routes.

## Architecture

### Core Components

#### 1. API Service (`src/services/api.ts`)
Centralized API service layer providing:
- **Authentication endpoints**: login, register, logout, token refresh, password reset
- **Token management**: setAuthToken, getAuthToken, getAuthHeaders
- **Auto token injection**: All API calls automatically include JWT token in headers

#### 2. Auth Context (`src/contexts/AuthContext.tsx`)
Global authentication state management using React Context API:
- **State**: user, isLoading, error
- **Methods**: login, register, logout, updateProfile
- **Auto-load**: Automatically loads user profile on mount if token exists
- **Notifications**: Toast notifications for auth events

#### 3. Protected Route (`src/components/ProtectedRoute.tsx`)
Route wrapper component that:
- Checks authentication status before rendering
- Shows loading spinner while verifying token
- Redirects to login if not authenticated
- Wraps all dashboard routes

#### 4. Login Page (`src/pages/Login.tsx`)
Dual-mode authentication UI:
- **Login mode**: Email/password authentication
- **Register mode**: Full registration with first name, last name, company
- **Loading states**: Disabled form fields and loading spinners during requests
- **Error handling**: Toast notifications for auth failures
- **Responsive design**: Mobile-friendly with trust indicators

## Implementation Details

### Authentication Flow

```
┌─────────────┐
│   Login     │
│    Page     │
└──────┬──────┘
       │
       │ User submits credentials
       ▼
┌─────────────────┐
│  useAuth hook   │
│  login/register │
└────────┬────────┘
         │
         │ Calls API service
         ▼
┌──────────────────┐
│   api.ts         │
│  POST /auth/...  │
└────────┬─────────┘
         │
         │ Receives JWT token
         ▼
┌──────────────────┐
│  localStorage    │
│  Save token      │
└────────┬─────────┘
         │
         │ Load user profile
         ▼
┌──────────────────┐
│  AuthContext     │
│  Set user state  │
└────────┬─────────┘
         │
         │ Navigate to dashboard
         ▼
┌──────────────────┐
│  ProtectedRoute  │
│  Check auth      │
└────────┬─────────┘
         │
         │ Render protected content
         ▼
┌──────────────────┐
│    Dashboard     │
└──────────────────┘
```

### Token Management

**Storage**: JWT tokens are stored in `localStorage` with the key `token`

**Injection**: The API service automatically injects the token in Authorization header:
```typescript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

**Refresh**: Token refresh is handled automatically by the `refreshToken()` function

**Expiration**: When token expires, user is redirected to login page

### Protected Routes

All dashboard routes are wrapped with `ProtectedRoute`:
```tsx
<Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
<Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
<Route path="/repositories" element={<ProtectedRoute><Repositories /></ProtectedRoute>} />
<Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
```

## API Endpoints

### Authentication Endpoints

#### Login
```typescript
POST /api/auth/login
Body: { email: string, password: string }
Response: { access_token: string, user: User }
```

#### Register
```typescript
POST /api/auth/register
Body: { 
  email: string, 
  password: string, 
  firstName: string, 
  lastName: string, 
  company?: string 
}
Response: { access_token: string, user: User }
```

#### Logout
```typescript
POST /api/auth/logout
Headers: { Authorization: Bearer <token> }
Response: { message: string }
```

#### Token Refresh
```typescript
POST /api/auth/refresh
Headers: { Authorization: Bearer <token> }
Response: { access_token: string }
```

#### Password Reset Request
```typescript
POST /api/auth/reset-password
Body: { email: string }
Response: { message: string }
```

#### Password Reset Confirmation
```typescript
POST /api/auth/reset-password/confirm
Body: { token: string, newPassword: string }
Response: { message: string }
```

## User Interface Features

### Login Mode
- Email input with validation
- Password input with masked characters
- Loading spinner during authentication
- Error messages via toast notifications
- "Forgot password?" link
- Switch to registration mode

### Registration Mode
- First name and last name fields
- Optional company field
- Email validation
- Password requirements (min 8 characters)
- Loading states on submit
- Switch back to login mode

### Trust Indicators
- "Secure" badge with shield icon
- "Encrypted" badge with lock icon
- Professional, trustworthy design

## Error Handling

All authentication operations include comprehensive error handling:

```typescript
try {
  await login({ email, password });
  navigate("/dashboard");
} catch (error) {
  console.error('Login failed:', error);
  // Toast notification shown by AuthContext
}
```

Errors are displayed as toast notifications using Sonner:
- Login failures: "Invalid credentials" or network errors
- Registration failures: Email already exists, validation errors
- Token refresh failures: Automatic logout and redirect

## Usage in Components

### Accessing Auth State
```typescript
import { useAuth } from "@/contexts/AuthContext";

function MyComponent() {
  const { user, isLoading, login, logout } = useAuth();
  
  if (isLoading) return <div>Loading...</div>;
  if (!user) return <div>Not authenticated</div>;
  
  return (
    <div>
      <p>Welcome, {user.firstName}!</p>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Making Authenticated API Calls
```typescript
import { getRepositories } from "@/services/api";

// Token is automatically included in the request
const repos = await getRepositories({ page: 1, perPage: 10 });
```

## Next Steps

### Immediate Tasks
1. ✅ Login page with AuthContext integration
2. ✅ Protected routes for dashboard
3. ✅ AuthProvider wrapping the app
4. ⏳ Add "Forgot Password" modal/flow
5. ⏳ Implement remember me functionality
6. ⏳ Add session timeout warnings

### Integration Tasks
1. ⏳ Update Repositories page with useRepositories hook
2. ⏳ Update Reports page with API service
3. ⏳ Update Settings page with user profile management
4. ⏳ Add notification system to header
5. ⏳ Implement logout functionality in header

### Enhancement Tasks
1. ⏳ Add OAuth providers (GitHub, Google)
2. ⏳ Implement 2FA/MFA support
3. ⏳ Add account verification email flow
4. ⏳ Session management across multiple tabs
5. ⏳ Token auto-refresh before expiration

## Testing

### Manual Testing Checklist
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Register new account
- [ ] Register with existing email
- [ ] Access protected route when logged out
- [ ] Access protected route when logged in
- [ ] Logout functionality
- [ ] Token persistence after page refresh
- [ ] Token expiration handling

### Automated Testing (To Implement)
- Unit tests for auth service functions
- Integration tests for login/register flows
- E2E tests for protected route access
- Token management edge cases

## Security Considerations

### Current Implementation
- ✅ JWT token stored in localStorage
- ✅ HTTPS required in production
- ✅ Token in Authorization header (not URL)
- ✅ Password min length requirement
- ✅ CORS configured on backend

### Future Enhancements
- ⏳ HttpOnly cookies for token storage
- ⏳ CSRF protection
- ⏳ Rate limiting on login attempts
- ⏳ Account lockout after failed attempts
- ⏳ Password strength requirements
- ⏳ Session invalidation on logout

## Configuration

### Environment Variables
Create a `.env` file with:
```
VITE_API_BASE_URL=http://152.67.4.15:5000
VITE_SOCKET_URL=http://152.67.4.15:5000
```

### Backend API URL
Update `src/services/api.ts` if backend URL changes:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://152.67.4.15:5000";
```

## Troubleshooting

### Common Issues

**Issue**: "Cannot find module './contexts/AuthContext'"
- **Solution**: Ensure AuthContext.tsx is created in src/contexts/

**Issue**: Login succeeds but redirects back to login
- **Solution**: Check if token is being saved correctly in localStorage
- **Solution**: Verify ProtectedRoute is checking authentication correctly

**Issue**: "401 Unauthorized" on API calls
- **Solution**: Check if token is being included in headers
- **Solution**: Verify token hasn't expired

**Issue**: User profile not loading after login
- **Solution**: Check if `/api/auth/profile` endpoint is working
- **Solution**: Verify token is valid

## Code Locations

- **API Service**: `src/services/api.ts`
- **Auth Context**: `src/contexts/AuthContext.tsx`
- **Login Page**: `src/pages/Login.tsx`
- **Protected Route**: `src/components/ProtectedRoute.tsx`
- **App Router**: `src/App.tsx`
- **Type Definitions**: `src/services/api.ts` (at top of file)

## Support

For issues or questions:
1. Check this guide first
2. Review console errors in browser DevTools
3. Check network tab for API request/response details
4. Verify backend is running and accessible
5. Check backend logs for authentication errors
