# Archived Authentication & Session Managers

This directory contains deprecated authentication and session management implementations that have been consolidated into the unified security namespace at `dreamos/core/security/`.

## Archived Files

### 1. legacy_auth_manager.py
- **Original Location**: `src/auth/manager.py`
- **Purpose**: Legacy authentication management
- **Features**:
  - Basic user authentication
  - Password hashing
  - User registration
- **Replacement**: Use `dreamos.core.security.auth_manager.AuthManager`

### 2. core_auth_manager.py
- **Original Location**: `dreamos/core/auth/manager.py`
- **Purpose**: Core authentication management
- **Features**:
  - Enhanced user authentication
  - Role-based access control
  - Token management
- **Replacement**: Use `dreamos.core.security.auth_manager.AuthManager`

### 3. legacy_session_manager.py
- **Original Location**: `src/auth/session.py`
- **Purpose**: Legacy session management
- **Features**:
  - Basic session tracking
  - Session timeout
  - Session cleanup
- **Replacement**: Use `dreamos.core.security.session_manager.SessionManager`

### 4. core_session_manager.py
- **Original Location**: `dreamos/core/auth/session.py`
- **Purpose**: Core session management
- **Features**:
  - Enhanced session tracking
  - Session metadata
  - Concurrent session handling
- **Replacement**: Use `dreamos.core.security.session_manager.SessionManager`

## Implementation Comparison

| Feature | Legacy | Core | Unified |
|---------|--------|------|---------|
| User Authentication | ✅ | ✅ | ✅ |
| Password Hashing | ✅ | ✅ | ✅ |
| Role Management | ❌ | ✅ | ✅ |
| Token Management | ❌ | ✅ | ✅ |
| Session Tracking | ✅ | ✅ | ✅ |
| Session Metadata | ❌ | ✅ | ✅ |
| Concurrent Access | ❌ | ✅ | ✅ |
| Security Features | Basic | Enhanced | Complete |

## Migration Notes

The unified security namespace provides:

- Enhanced authentication with role-based access control
- Robust token management and validation
- Comprehensive session tracking with metadata
- Thread-safe concurrent access
- Better error handling and logging
- Integration with the core security system

## Usage Example

```python
from dreamos.core.security.auth_manager import AuthManager
from dreamos.core.security.session_manager import SessionManager

# Initialize managers
auth_manager = AuthManager()
session_manager = SessionManager()

# Register and authenticate user
success, error = auth_manager.register_user("user", "password", {"role": "developer"})
success, error, token = auth_manager.authenticate("user", "password")

# Create and manage session
session_token = session_manager.create_session("user", {"ip": "127.0.0.1"})
session = session_manager.get_session(session_token)
```

## Migration Status

- [x] Files archived
- [x] Deprecation warnings added
- [x] Documentation updated
- [x] Imports checked for references

## Next Steps

1. Update any remaining imports to use the unified security namespace
2. Remove deprecated files once all references are updated
3. Update documentation to reflect the consolidated security system 