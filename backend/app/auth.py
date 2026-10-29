"""
Authentication module for StockTalk.
Validates Supabase-issued JWTs using JWKS (JSON Web Key Set).
"""
import time
import logging
from typing import Optional, Dict, Any
from functools import lru_cache

import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Cache JWKS for 1 hour (Supabase rotates keys periodically)
JWKS_CACHE_TTL = 3600
_jwks_cache: Dict[str, Any] = {"keys": [], "fetched_at": 0}


async def fetch_jwks() -> Dict[str, Any]:
    """Fetch JWKS from Supabase Auth endpoint."""
    global _jwks_cache

    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < JWKS_CACHE_TTL:
        return _jwks_cache

    jwks_url = settings.supabase_jwks_url or f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            _jwks_cache = {"keys": jwks.get("keys", []), "fetched_at": now}
            logger.info(f"Fetched JWKS with {len(jwks.get('keys', []))} keys")
            return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
        if _jwks_cache["keys"]:
            logger.warning("Using cached JWKS")
            return _jwks_cache
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


def get_signing_key(token: str) -> str:
    """Extract the signing key from JWKS based on token's kid header."""
    unverified_header = jwt.get_unverified_header(token)
    kid = unverified_header.get("kid")

    if not kid:
        raise JWTError("Token missing 'kid' header")

    jwks = _jwks_cache["keys"]
    for key in jwks:
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(key)

    # Key not in cache, fetch fresh JWKS
    # This is a fallback - in production you'd want to handle this more gracefully
    raise JWTError(f"Signing key not found for kid: {kid}")


async def verify_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a Supabase JWT token.
    Returns the decoded payload if valid.
    """
    try:
        # Get signing key
        key = get_signing_key(token)

        # Decode and verify
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience="authenticated",  # Supabase default audience
            options={"verify_exp": True}
        )

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTClaimsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token claims: {e}"
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency to get the current authenticated user.
    Validates JWT and returns User model from database.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    payload = await verify_supabase_jwt(token)

    # Extract user info from JWT
    supabase_uid = payload.get("sub")
    email = payload.get("email")
    role = payload.get("role", "shopkeeper")

    if not supabase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject"
        )

    # Find or create user in local database
    user = db.query(models.User).filter(models.User.supabase_uid == supabase_uid).first()

    if not user:
        # Create user from JWT claims (first login after Supabase signup)
        user = models.User(
            email=email,
            password_hash="supabase_managed",  # Placeholder
            role=role,
            status="active",
            supabase_uid=supabase_uid,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create business profile if needed
        # This will be completed via profile setup endpoint
    elif user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Optional authentication - returns None if no valid token."""
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*allowed_roles: str):
    """Dependency factory for role-based access control."""
    async def role_checker(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker


# Convenience dependencies
require_shopkeeper = require_role("shopkeeper", "admin")
require_vendor = require_role("vendor", "admin")
require_admin = require_role("admin")


async def get_business_profile(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> models.BusinessProfile:
    """Get the business profile for the current user."""
    profile = db.query(models.BusinessProfile).filter(
        models.BusinessProfile.user_id == user.id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found. Complete your profile setup."
        )

    return profile


async def get_shopkeeper_profile(
    profile: models.BusinessProfile = Depends(get_business_profile),
    user: models.User = Depends(require_shopkeeper)
) -> models.BusinessProfile:
    """Ensure the user is a shopkeeper and return their business profile."""
    return profile


async def get_vendor_profile(
    profile: models.BusinessProfile = Depends(get_business_profile),
    user: models.User = Depends(require_vendor)
) -> models.BusinessProfile:
    """Ensure the user is a vendor and return their business profile."""
    return profile