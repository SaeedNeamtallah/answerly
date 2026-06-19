## 26. Frontend Security Behavior

### Explanation

The frontend includes security-related behavior such as storing JWT access tokens in localStorage, adding Bearer tokens to API requests, decoding token expiration client-side, redirecting to login when tokens are missing or expired, clearing tokens after authentication failure, and hiding Security Center UI unless the user has an admin or security-engineer role.

### Path

`frontend/app.js`

```javascript
const ROLE_USER = 'user';
const ROLE_ADMIN = 'admin';
const ROLE_SECURITY_ENGINEER = 'security_engineer';
const ROLE_CYBERSECURITY_ENGINEER = 'cybersecurity_engineer';

function getAccessToken() {
    return (localStorage.getItem(ACCESS_TOKEN_KEY) || '').trim();
}

function parseJwtPayload(token) {
    const parts = String(token || '').split('.');
    if (parts.length !== 3) return null;
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = base64 + '='.repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded));
}

function isTokenExpired(token) {
    const payload = parseJwtPayload(token);
    if (!payload || typeof payload.exp !== 'number') return true;
    return Date.now() >= payload.exp * 1000;
}
```

```javascript
function withAuthHeaders(extraHeaders = {}) {
    const token = getAccessToken();
    const headers = { ...extraHeaders };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    return headers;
}

function canAccessSecurityCenter(user = state.currentUser) {
    const roles = normalizeUserRoles(user);
    return roles.includes(ROLE_SECURITY_ENGINEER)
        || roles.includes(ROLE_CYBERSECURITY_ENGINEER)
        || roles.includes(ROLE_ADMIN);
}
```

---
