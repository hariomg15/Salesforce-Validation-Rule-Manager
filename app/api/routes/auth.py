import base64
import hashlib
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_session
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.oauth_session import OAuthSession


router = APIRouter()


def build_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("utf-8")).digest()
    ).rstrip(b"=").decode("utf-8")
    return verifier, challenge


@router.get("/login-url")
async def get_login_url(db: Session = Depends(get_db)) -> dict[str, str]:
    session = OAuthSession(status="pending")
    db.add(session)
    db.commit()
    db.refresh(session)

    verifier, challenge = build_pkce_pair()

    query_string = urlencode(
        {
            "response_type": "code",
            "client_id": settings.salesforce_client_id,
            "redirect_uri": settings.effective_salesforce_redirect_uri,
            "scope": "api refresh_token id",
            "state": session.id,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )

    return {
        "login_url": f"{settings.salesforce_login_url}/services/oauth2/authorize?{query_string}",
        "session_id": session.id,
        "code_verifier": verifier,
    }


@router.get("/salesforce/login")
async def salesforce_login(db: Session = Depends(get_db)) -> RedirectResponse:
    payload = await get_login_url(db)
    response = RedirectResponse(url=payload["login_url"], status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="sf_pkce_verifier",
        value=payload["code_verifier"],
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        key="sf_oauth_state",
        value=payload["session_id"],
        httponly=True,
        samesite="lax",
    )
    return response


@router.post("/dev-login")
async def dev_login(db: Session = Depends(get_db)) -> dict[str, str]:
    session = OAuthSession(
        salesforce_user_id="local-dev-user",
        salesforce_org_id="local-dev-org",
        salesforce_instance_url="https://login.salesforce.com",
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    access_token = create_access_token(session.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "session_id": session.id,
    }


@router.get("/callback")
async def salesforce_callback(
    code: str = Query(...),
    state: str = Query(...),
    sf_pkce_verifier: str | None = Cookie(default=None),
    sf_oauth_state: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if not sf_pkce_verifier or not sf_oauth_state or sf_oauth_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing or invalid PKCE state",
        )

    session = db.get(OAuthSession, state)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth state",
        )

    token_url = f"{settings.salesforce_login_url}/services/oauth2/token"
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": settings.salesforce_client_id,
        "client_secret": settings.salesforce_client_secret,
        "redirect_uri": settings.effective_salesforce_redirect_uri,
        "code": code,
        "code_verifier": sf_pkce_verifier,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        token_response = await client.post(token_url, data=token_payload)
        if token_response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=token_response.text,
            )

        token_data = token_response.json()
        identity_data: dict[str, str] = {}
        identity_url = token_data.get("id")

        if identity_url:
            identity_response = await client.get(
                identity_url,
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            if identity_response.status_code < 400:
                identity_data = identity_response.json()

    session.access_token = token_data.get("access_token")
    session.refresh_token = token_data.get("refresh_token")
    session.salesforce_instance_url = token_data.get("instance_url")
    session.salesforce_user_id = identity_data.get("user_id")
    session.salesforce_org_id = identity_data.get("organization_id")
    session.status = "active"
    db.add(session)
    db.commit()

    app_token = create_access_token(session.id)
    redirect_url = f"{settings.frontend_origin}/?token={app_token}&session_id={session.id}"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie("sf_pkce_verifier")
    response.delete_cookie("sf_oauth_state")
    return response


@router.get("/me")
async def get_current_login(
    session: OAuthSession = Depends(get_current_session),
) -> dict[str, str | None]:
    return {
        "session_id": session.id,
        "status": session.status,
        "salesforce_user_id": session.salesforce_user_id,
        "salesforce_org_id": session.salesforce_org_id,
        "salesforce_instance_url": session.salesforce_instance_url,
    }
