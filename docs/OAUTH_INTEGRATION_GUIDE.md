# OAuth Integration Guide - GitHub & GitVerse

**Status:** 📋 Planned (Requires GitHub App Registration)
**Priority:** High
**Complexity:** Medium-High

---

## Overview

OAuth integration allows users to connect their GitHub/GitVerse accounts to Repa, enabling:
- ✅ Automatic repository cloning
- ✅ Git operations with user's permissions
- ✅ Access to private repositories
- ✅ Commit/push changes back to remote

---

## Prerequisites

### 1. GitHub App Registration

**Register at:** https://github.com/settings/apps/new

**Required settings:**
```
App name: Repa AI
Homepage URL: https://your-domain.com
Callback URL: https://your-domain.com/api/v1/auth/github/callback
                (for local dev: http://localhost:8000/api/v1/auth/github/callback)

Permissions:
- Repository: Read & Write
- Contents: Read & Write
- Metadata: Read-only
- Pull requests: Read & Write

Subscribe to events:
- Push
- Pull request
```

**After registration:**
- Save **Client ID**
- Generate and save **Client Secret**
- Download private key (for GitHub App API)

### 2. Environment Variables

Add to `.env`:
```bash
# GitHub OAuth
GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem

# GitVerse OAuth (if applicable)
GITVERSE_CLIENT_ID=xxxxxxxxxxxx
GITVERSE_CLIENT_SECRET=xxxxxxxxxxxx
```

---

## Database Schema

### New Table: `oauth_connections`

```sql
CREATE TABLE oauth_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL, -- 'github', 'gitverse', 'gitlab'

    -- OAuth data
    provider_user_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    avatar_url VARCHAR(500),

    -- Tokens (encrypted)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,

    -- Scopes granted
    scopes TEXT[], -- ['repo', 'user', 'write:repo_hook']

    -- Metadata
    provider_metadata JSONB, -- Raw response from provider

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(user_id, provider, provider_user_id)
);

CREATE INDEX idx_oauth_user_provider ON oauth_connections(user_id, provider);
CREATE INDEX idx_oauth_provider_user ON oauth_connections(provider, provider_user_id);
```

### Migration

```bash
# Generate migration
cd backend
alembic revision -m "add oauth_connections table"

# Apply migration
alembic upgrade head
```

---

## Backend Implementation

### 1. Add Dependencies

```bash
# backend/requirements.txt
httpx==0.24.1           # For HTTP requests to GitHub API
cryptography==41.0.4    # For token encryption
python-jose[cryptography]==3.3.0  # JWT handling
```

### 2. OAuth Service

```python
# backend/src/services/oauth_service.py

import httpx
from typing import Optional
from cryptography.fernet import Fernet
from src.core.config import settings

class OAuthService:
    def __init__(self):
        self.github_client_id = settings.GITHUB_CLIENT_ID
        self.github_client_secret = settings.GITHUB_CLIENT_SECRET
        self.cipher = Fernet(settings.ENCRYPTION_KEY)

    def get_github_auth_url(self, state: str) -> str:
        """Generate GitHub OAuth URL"""
        params = {
            'client_id': self.github_client_id,
            'redirect_uri': f'{settings.BACKEND_URL}/api/v1/auth/github/callback',
            'scope': 'repo user write:repo_hook',
            'state': state,  # CSRF protection
        }
        query = '&'.join(f'{k}={v}' for k, v in params.items())
        return f'https://github.com/login/oauth/authorize?{query}'

    async def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://github.com/login/oauth/access_token',
                json={
                    'client_id': self.github_client_id,
                    'client_secret': self.github_client_secret,
                    'code': code,
                },
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            return response.json()

    async def get_github_user(self, access_token: str) -> dict:
        """Get GitHub user profile"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://api.github.com/user',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/vnd.github+json',
                }
            )
            response.raise_for_status()
            return response.json()

    def encrypt_token(self, token: str) -> str:
        """Encrypt access token before storing"""
        return self.cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt access token for use"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()
```

### 3. API Endpoints

```python
# backend/src/api/v1/oauth.py

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import secrets

from src.db.base import get_db
from src.db.models.oauth import OAuthConnection
from src.services.oauth_service import OAuthService
from src.api.v1.auth import get_current_user
from src.db.models.user import User

router = APIRouter(prefix="/auth", tags=["OAuth"])
oauth_service = OAuthService()

# In-memory state storage (use Redis in production)
_oauth_states = {}

@router.get("/github/login")
async def github_login(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Initiate GitHub OAuth flow.
    Returns URL to redirect user to GitHub.
    """
    # Generate CSRF token
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        'user_id': str(current_user.id),
        'expires': datetime.utcnow() + timedelta(minutes=10)
    }

    auth_url = oauth_service.get_github_auth_url(state)

    return {
        'auth_url': auth_url,
        'state': state
    }

@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle GitHub OAuth callback.
    Exchange code for token and save connection.
    """
    # Verify state (CSRF protection)
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    user_id = _oauth_states[state]['user_id']
    del _oauth_states[state]

    try:
        # Exchange code for token
        token_data = await oauth_service.exchange_code_for_token(code)
        access_token = token_data['access_token']

        # Get GitHub user info
        github_user = await oauth_service.get_github_user(access_token)

        # Save or update OAuth connection
        connection = OAuthConnection(
            user_id=user_id,
            provider='github',
            provider_user_id=str(github_user['id']),
            username=github_user['login'],
            email=github_user.get('email'),
            avatar_url=github_user.get('avatar_url'),
            access_token=oauth_service.encrypt_token(access_token),
            scopes=token_data.get('scope', '').split(','),
            provider_metadata=github_user,
        )

        db.add(connection)
        await db.commit()

        # Redirect to frontend success page
        return RedirectResponse(
            url=f'{settings.FRONTEND_URL}/settings?oauth=success&provider=github'
        )

    except Exception as e:
        print(f"OAuth error: {e}")
        return RedirectResponse(
            url=f'{settings.FRONTEND_URL}/settings?oauth=error&message={str(e)}'
        )

@router.get("/connections")
async def list_connections(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """List user's OAuth connections"""
    result = await db.execute(
        select(OAuthConnection)
        .where(OAuthConnection.user_id == current_user.id)
        .where(OAuthConnection.is_active == True)
    )
    connections = result.scalars().all()

    return [{
        'id': str(conn.id),
        'provider': conn.provider,
        'username': conn.username,
        'avatar_url': conn.avatar_url,
        'connected_at': conn.created_at.isoformat(),
    } for conn in connections]

@router.delete("/connections/{connection_id}")
async def disconnect(
    connection_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Disconnect OAuth provider"""
    result = await db.execute(
        select(OAuthConnection)
        .where(OAuthConnection.id == connection_id)
        .where(OAuthConnection.user_id == current_user.id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    connection.is_active = False
    await db.commit()

    return {'success': True}
```

### 4. Register Router

```python
# backend/src/main.py

from src.api.v1 import oauth

app.include_router(oauth.router, prefix="/api/v1")
```

---

## Frontend Implementation

### 1. OAuth Flow Hook

```typescript
// frontend/src/hooks/useOAuth.ts

export function useGitHubOAuth() {
  const [isConnecting, setIsConnecting] = useState(false);

  const connectGitHub = async () => {
    setIsConnecting(true);

    try {
      // Step 1: Get GitHub auth URL
      const response = await apiClient.get('/api/v1/auth/github/login');
      const { auth_url } = response.data;

      // Step 2: Open popup window
      const popup = window.open(
        auth_url,
        'github-oauth',
        'width=600,height=700'
      );

      // Step 3: Listen for callback
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return;

        if (event.data.type === 'oauth-success') {
          toast.success('GitHub подключен успешно!');
          popup?.close();
          window.removeEventListener('message', handleMessage);
          // Refresh connections list
          queryClient.invalidateQueries(['oauth-connections']);
        } else if (event.data.type === 'oauth-error') {
          toast.error(`Ошибка: ${event.data.message}`);
          popup?.close();
        }
      };

      window.addEventListener('message', handleMessage);

    } catch (error) {
      toast.error('Ошибка при подключении GitHub');
    } finally {
      setIsConnecting(false);
    }
  };

  return { connectGitHub, isConnecting };
}
```

### 2. OAuth Callback Page

```typescript
// frontend/src/pages/OAuthCallback.tsx

export function OAuthCallback() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const oauth = params.get('oauth');
    const provider = params.get('provider');
    const message = params.get('message');

    if (oauth === 'success') {
      // Notify parent window
      window.opener?.postMessage({
        type: 'oauth-success',
        provider
      }, window.location.origin);
    } else if (oauth === 'error') {
      window.opener?.postMessage({
        type: 'oauth-error',
        message
      }, window.location.origin);
    }
  }, []);

  return (
    <div className="flex items-center justify-center h-screen">
      <Loader2 className="w-8 h-8 animate-spin" />
      <p>Завершение подключения...</p>
    </div>
  );
}
```

### 3. Update OrgSettings

```typescript
// frontend/src/app/components/OrgSettings.tsx

const { connectGitHub, isConnecting } = useGitHubOAuth();

const handleIntegrationAction = (id: string, name: string, status: string) => {
  if (status === 'connected') {
    // Show settings modal
    toast.info(`Настройки ${name}`);
  } else {
    // Initiate OAuth
    if (id === 'github') {
      connectGitHub();
    } else {
      toast.info(`OAuth для ${name} будет доступен скоро`);
    }
  }
};
```

---

## Security Considerations

### 1. Token Storage
- ✅ Encrypt tokens at rest using Fernet (AES-128)
- ✅ Store encryption key in environment variable
- ✅ Never log decrypted tokens
- ✅ Rotate encryption keys periodically

### 2. CSRF Protection
- ✅ Use `state` parameter in OAuth flow
- ✅ Verify state matches on callback
- ✅ State expires after 10 minutes
- ✅ Store states in Redis (not in-memory for production)

### 3. Token Refresh
```python
async def refresh_github_token(connection: OAuthConnection):
    """Refresh expired GitHub token"""
    # GitHub tokens don't expire, but other providers might
    # Implement refresh logic if needed
    pass
```

### 4. Scope Validation
- Only request minimum necessary scopes
- Display granted scopes to user
- Allow users to revoke connections

---

## Testing

### 1. Manual Testing (with real GitHub App)

```bash
# 1. Start backend
cd backend
uvicorn src.main:app --reload --port 8000

# 2. Start frontend
cd frontend
npm run dev

# 3. Navigate to /settings
# 4. Click "ПОДКЛЮЧИТЬ" on GitHub
# 5. Complete OAuth flow
# 6. Verify connection appears in list
```

### 2. Unit Tests

```python
# tests/test_oauth.py

async def test_github_login_generates_url():
    response = client.get('/api/v1/auth/github/login')
    assert response.status_code == 200
    assert 'auth_url' in response.json()
    assert 'github.com/login/oauth/authorize' in response.json()['auth_url']

async def test_oauth_callback_creates_connection():
    # Mock GitHub API responses
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value.json.return_value = {
            'access_token': 'gho_xxxx',
            'scope': 'repo,user'
        }

        response = client.get(
            '/api/v1/auth/github/callback',
            params={'code': 'test_code', 'state': 'test_state'}
        )

        assert response.status_code == 302  # Redirect
```

---

## Production Deployment

### 1. Environment Setup

```bash
# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to production .env
ENCRYPTION_KEY=your_generated_key_here
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
BACKEND_URL=https://api.repa.ai
FRONTEND_URL=https://repa.ai
```

### 2. Database Migration

```bash
# Production
alembic upgrade head
```

### 3. Update Callback URL

Register production callback URL in GitHub App settings:
```
https://api.repa.ai/api/v1/auth/github/callback
```

---

## Roadmap

### Phase 1: GitHub (MVP) ✅
- GitHub OAuth flow
- Basic token storage
- Connect/disconnect UI

### Phase 2: GitVerse
- Similar to GitHub
- Adjust for GitVerse API differences

### Phase 3: Multiple Providers
- GitLab
- Bitbucket
- Support multiple connections per provider

### Phase 4: Advanced Features
- Token refresh automation
- Webhook integration
- Organization-level connections
- Team permissions

---

## Troubleshooting

### Error: "redirect_uri_mismatch"
**Fix:** Update callback URL in GitHub App settings to match `BACKEND_URL/api/v1/auth/github/callback`

### Error: "bad_verification_code"
**Fix:** Code already used or expired. User must re-initiate OAuth flow.

### Error: "Token encryption failed"
**Fix:** Verify `ENCRYPTION_KEY` is valid Fernet key (44 chars, base64)

---

## Related Documentation

- [GitHub OAuth Apps](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps)
- [GitVerse API](https://gitverse.ru/docs/api)
- [FastAPI OAuth2](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

---

**Document Created:** 2026-02-06
**Author:** Claude Sonnet 4.5
**Status:** Implementation Guide

**Next Steps:**
1. Register GitHub App
2. Add environment variables
3. Run database migration
4. Test OAuth flow locally
5. Deploy to production
