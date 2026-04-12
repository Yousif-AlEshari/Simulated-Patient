# JWT Integration Plan

**Date Created:** April 8, 2026  
**Status:** Planning Phase

---

## Executive Summary

Your application already has basic JWT token generation for login/register. This plan completes the JWT integration by adding:
- **Token verification/validation** for protected routes
- **Token refresh mechanism** for better security
- **Permission-based access control** (roles/scopes)
- **Middleware for automatic token extraction**
- **Frontend token management** (storage, refresh, retry)
- **Security hardening** (token expiration, secret rotation, blacklisting)

---

## Current State Assessment

### ✅ What's Already Implemented
- JWT token generation (`create_access_token()`)
- Password hashing with bcrypt
- User registration & login endpoints
- Basic `Token` model response
- FastAPI CORS middleware

### ❌ What's Missing
- **Token verification** - routes don't verify incoming tokens
- **Token extraction** from Authorization header
- **Refresh token mechanism** - one-time use refresh tokens
- **Role-based access control (RBAC)** - only basic user model
- **Protected routes** - endpoints need authentication guards
- **Token blacklist** - no revocation mechanism
- **Frontend token handling** - localStorage/cookie management
- **Token validation middleware**

---

## Implementation Phases

### Phase 1: Backend Token Verification & Dependencies (🔥 High Priority)

**Objective:** Add token validation to protected routes

#### 1.1 Update Dependencies
```text
Add to requirements.txt:
- python-jose[cryptography]>=3.3.0
- passlib[bcrypt]>=1.7.4
- python-multipart>=0.0.5
```

#### 1.2 Create Token Verification Module
**File:** `api/auth_utils.py`

Add:
- `verify_token()` - decode & validate JWT
- `get_current_user()` - FastAPI dependency to extract user from token
- `TokenData` model - validated token claims
- Exception handling for invalid/expired tokens

**Key Functions:**
```python
def verify_token(token: str) -> TokenData:
    """Decode and validate JWT token"""
    # Decode token
    # Verify signature, expiration, claims
    # Return TokenData with user info
    
def get_current_user(token: str = Depends(HTTPBearer())) -> User:
    """Dependency for protected routes"""
    # Extract token from header
    # Verify token
    # Fetch user from DB
    # Return current user
```

#### 1.3 Update Auth Models
**File:** `api/models.py`

Add/Update:
```python
class TokenData(BaseModel):
    email: str
    exp: datetime
    iat: datetime
    scope: str = "read:write"

class Token(BaseModel):
    access_token: str
    refresh_token: str  # NEW
    token_type: str
    expires_in: int  # seconds
    user: UserResponse

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str  # NEW
```

---

### Phase 2: Refresh Token System (🟡 Medium Priority)

**Objective:** Implement secure token refresh flow

#### 2.1 Update User Model
**File:** `api/db_models.py`

Add to `User` class:
```python
refresh_token = Column(String, nullable=True)  # Hashed
refresh_token_expires = Column(DateTime, nullable=True)
role = Column(String, default="trainee")  # trainee, evaluator, admin
is_active = Column(Boolean, default=True)
```

#### 2.2 Refresh Token Endpoints
**File:** `api/routes/auth.py`

Add new endpoints:
```python
@router.post("/refresh")
def refresh_access_token(refresh_token: str) -> Token:
    """Exchange refresh token for new access token"""
    # Verify refresh token from DB
    # Check expiration
    # Generate new access token
    # Update refresh token (rotate)
    # Return new tokens

@router.post("/logout")
def logout_user(current_user: User = Depends(get_current_user)):
    """Invalidate refresh token"""
    # Set refresh_token to NULL in DB
    # Return success
```

**Token Expiry Strategy:**
- Access Token: 15-60 minutes
- Refresh Token: 7-30 days
- Session Expiry: configurable per route

---

### Phase 3: Protected Routes & RBAC (🟡 Medium Priority)

**Objective:** Secure API endpoints with role-based access

#### 3.1 Create Authorization Module
**File:** `api/auth_utils.py` (expand)

Add:
```python
async def get_current_user(token: str = Depends(HTTPBearer())) -> User:
    """Extract & validate current user from token"""
    
async def require_role(*roles: str):
    """Decorator/dependency for role-based access"""
    # Check if current_user.role in allowed roles
    
async def require_permission(permission: str):
    """Fine-grained permission checking"""
```

#### 3.2 Protect Existing Routes
**Files to Update:**
- `api/routes/chat.py` - require "trainee" role
- `api/routes/patient_eval.py` - require "evaluator" role  
- `api/routes/trainee_eval.py` - require "evaluator" role
- `api/routes/admin.py` - require "admin" role
- `api/routes/session.py` - require authentication

**Pattern:**
```python
@router.post("/chat/start")
async def start_chat(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
):
    """Protected route - only authenticated users"""
    # Store session with user_id: current_user.id
    # ...
```

#### 3.3 User Roles Definition
**File:** `api/models.py` (add Enum)

```python
class UserRole(str, Enum):
    TRAINEE = "trainee"      # Can take patient interactions
    EVALUATOR = "evaluator"   # Can evaluate sessions
    ADMIN = "admin"           # Full system access
```

---

### Phase 4: Token Blacklisting & Revocation (🟢 Low Priority - Optional)

**Objective:** Implement logout & token revocation

#### 4.1 Option A: Database Blacklist (Recommended)
**File:** `api/db_models.py`

Add:
```python
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(String, primary_key=True)
    token = Column(String, unique=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Auto-cleanup
```

#### 4.2 Option B: Redis Cache (Performance Alternative)
- Fast in-memory storage
- Auto-expiration (TTL)
- No DB queries needed

#### 4.3 Logout Handler
```python
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # Add current token to blacklist
    # Return 200 OK
```

---

### Phase 5: Frontend Token Management (🟡 Medium Priority)

**Objective:** Implement secure token storage & refresh flow

#### 5.1 Token Storage Decisions
| Method              | Pros                   | Cons                      |
| ------------------- | ---------------------- | ------------------------- |
| **localStorage**    | Persistent, simple     | XSS vulnerable            |
| **sessionStorage**  | Session-bound          | Lost on refresh           |
| **Memory + Cookie** | XSS safe, auto-refresh | Requires refresh logic    |
| **httpOnly Cookie** | Most secure            | CSRF risk, manual refresh |

**Recommendation:** Memory + Refresh Cookie pattern

#### 5.2 Frontend Context/Hook
**File:** `frontend-react/src/context/AuthContext.jsx` (update)

```javascript
// Token storage
const token = localStorage.getItem("access_token");
const refreshToken = localStorage.getItem("refresh_token");

// Auto-refresh logic
setInterval(() => {
  if (tokenExpiredSoon()) {
    refreshAccessToken();
  }
}, 60000); // Check every minute

// Logout handler
logout() -> clear tokens -> redirect to /login

// Token injection in requests
headers: {
  "Authorization": `Bearer ${token}`
}
```

#### 5.3 Fetch Interceptor
```javascript
// Add auth header to all requests
// Catch 401 -> auto-refresh -> retry request
// Catch 401 on refresh -> logout user
```

#### 5.4 Protected Route Components
```javascript
<ProtectedRoute 
  requiredRole="evaluator" 
  component={EvaluationPage} 
/>
```

---

### Phase 6: Security Hardening (🟢 Low Priority - Optional)

#### 6.1 Environment Variables
**File:** `.env`

```bash
SECRET_KEY=<generate with openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_AUDIENCE="simulated-patient-api"
JWT_ISSUER="simulated-patient-system"
```

#### 6.2 Token Claims Enhancement
```python
{
  "sub": "user_id",           # Subject
  "email": "user@example.com", # Email
  "role": "trainee",          # Role
  "iat": 1234567890,          # Issued at
  "exp": 1234571490,          # Expiration
  "aud": "simulated-patient-api",  # Audience
  "iss": "simulated-patient-system", # Issuer
  "scope": "read:write",      # Permissions
  "jti": "unique-token-id"    # JWT ID (for blacklist)
}
```

#### 6.3 Rotation Strategy
- Generate new `SECRET_KEY` periodically
- Support key versioning (old keys still valid for grace period)
- Auto-logout users on critical updates

#### 6.4 HTTPS Requirement
- Force HTTPS in production
- Secure cookies (`httpOnly=True`)
- CSRF protection if using cookies

---

## Implementation Order & Sprints

### Sprint 1: Core Token Verification (Weeks 1-2)
1. ✅ Add token verification module (`api/auth_utils.py`)
2. ✅ Update models (`api/models.py`)
3. ✅ Protect critical routes (chat, eval)
4. ✅ Update auth endpoints with error handling
5. 🧪 Unit test token validation

### Sprint 2: Refresh Token & RBAC (Weeks 3-4)
1. ✅ Update User model with refresh tokens & roles
2. ✅ Implement refresh endpoint
3. ✅ Add role-based access control
4. ✅ Protect all routes with roles
5. 🧪 Integration test refresh flow

### Sprint 3: Frontend Integration (Weeks 5-6)
1. ✅ Update AuthContext with token logic
2. ✅ Implement auto-refresh (15 min before expiry)
3. ✅ Add logout functionality
4. ✅ Implement protected route components
5. 🧪 E2E test login → interact → logout flow

### Sprint 4: Security & Hardening (Week 7)
1. ✅ Add token blacklist (optional)
2. ✅ Environment variable validation
3. ✅ HTTPS enforcement
4. ✅ Rate limiting on auth endpoints
5. 🧪 Security audit & penetration testing

---

## File Checklist

### Backend
- [ ] `api/auth_utils.py` (NEW) - Token verification & dependencies
- [ ] `api/models.py` (UPDATE) - Add TokenData, UserRole, update Token
- [ ] `api/db_models.py` (UPDATE) - Add refresh_token, role, is_active to User
- [ ] `api/routes/auth.py` (UPDATE) - Add refresh & logout endpoints
- [ ] `api/routes/chat.py` (UPDATE) - Protect endpoints
- [ ] `api/routes/patient_eval.py` (UPDATE) - Protect endpoints
- [ ] `api/routes/trainee_eval.py` (UPDATE) - Protect endpoints
- [ ] `api/routes/admin.py` (UPDATE) - Protect with admin role
- [ ] `api/routes/session.py` (UPDATE) - Protect endpoints
- [ ] `.env.example` (NEW) - Template for JWT secrets
- [ ] `requirements.txt` (UPDATE) - Add JWT dependencies

### Frontend
- [ ] `frontend-react/src/context/AuthContext.jsx` (UPDATE) - Token management
- [ ] `frontend-react/src/hooks/useAuth.js` (NEW) - Auth hook with refresh logic
- [ ] `frontend-react/src/hooks/useFetch.js` (NEW) - Fetch wrapper with token injection
- [ ] `frontend-react/src/components/ProtectedRoute.jsx` (NEW) - Role-based routing
- [ ] `frontend-react/src/services/authService.js` (NEW) - API calls for auth
- [ ] `frontend-react/src/pages/LoginPage.jsx` (UPDATE) - Handle token storage
- [ ] `frontend-react/src/pages/LogoutPage.jsx` (NEW) - Clear tokens & redirect

### Documentation
- [ ] `JWT_INTEGRATION_GUIDE.md` (NEW) - Step-by-step implementation guide
- [ ] API documentation update in FastAPI docs
- [ ] Frontend auth flow diagram

---

## Testing Strategy

### Backend Tests
```python
# Test token creation
# Test token expiration
# Test invalid token handling
# Test refresh token flow
# Test role-based access
# Test concurrent requests
```

### Frontend Tests
```javascript
// Test token storage
// Test auto-refresh logic
// Test protected routes
// Test logout clears tokens
// Test error handling on 401
```

### Integration Tests
```
Flow: Register → Login → Store Token → Access Protected Resource → Logout
```

---

## Potential Risks & Mitigations

| Risk                         | Impact                      | Mitigation                           |
| ---------------------------- | --------------------------- | ------------------------------------ |
| Token theft                  | Complete session compromise | Use httpOnly cookies, HTTPS only     |
| Token expiration not handled | User locked out mid-session | Auto-refresh 15min before expiry     |
| Secret key exposure          | All tokens compromised      | Use strong, rotating keys in .env    |
| Role bypass                  | Unauthorized access         | Verify role on every protected route |
| Token blacklist not checked  | Logout ineffective          | Redis or DB lookup on validation     |

---

## Success Criteria

✅ All protected routes require valid JWT token  
✅ Tokens expire and require refresh  
✅ Role-based access control enforced  
✅ Logout invalidates tokens  
✅ Frontend securely stores & manages tokens  
✅ Auto-refresh prevents session expiry  
✅ 401 errors properly handled  
✅ Security audit passed  
✅ <100ms token validation latency  

---

## Next Steps

1. **Review this plan** with your team
2. **Prioritize phases** based on project timeline
3. **Create user stories** from each phase
4. **Start Sprint 1** with token verification
5. **Reference** `JWT_INTEGRATION_GUIDE.md` during implementation

