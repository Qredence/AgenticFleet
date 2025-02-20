import base64
import os
import urllib.parse
from typing import Dict, List, Optional, Tuple

import httpx
from chainlit.secret import random_secret
from chainlit.user import User
from fastapi import HTTPException


class OAuthProvider:
    id: str
    env: List[str]
    client_id: str
    client_secret: str
    authorize_url: str
    authorize_params: Dict[str, str]
    default_prompt: Optional[str] = None

    def is_configured(self):
        return all([os.environ.get(env) for env in self.env])

    async def get_token(self, code: str, url: str) -> str:
        raise NotImplementedError

    async def get_user_info(self, token: str) -> Tuple[Dict[str, str], User]:
        raise NotImplementedError

    def get_env_prefix(self) -> str:
        """Return environment prefix, like AZURE_AD."""

        return self.id.replace("-", "_").upper()

    def get_prompt(self) -> Optional[str]:
        """Return OAuth prompt param."""
        if prompt := os.environ.get(f"OAUTH_{self.get_env_prefix()}_PROMPT"):
            return prompt

        if prompt := os.environ.get("OAUTH_PROMPT"):
            return prompt

        return self.default_prompt


class GithubOAuthProvider(OAuthProvider):
    id = "github"
    env = ["OAUTH_GITHUB_CLIENT_ID", "OAUTH_GITHUB_CLIENT_SECRET"]
    authorize_url = "https://github.com/login/oauth/authorize"

    def __init__(self):
        self.client_id = os.environ.get("OAUTH_GITHUB_CLIENT_ID")
        self.client_secret = os.environ.get("OAUTH_GITHUB_CLIENT_SECRET")
        self.authorize_params = {
            "scope": "user:email",
        }

        if prompt := self.get_prompt():
            self.authorize_params["prompt"] = prompt

    async def get_token(self, code: str, url: str):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data=payload,
            )
            response.raise_for_status()
            content = urllib.parse.parse_qs(response.text)
            token = content.get("access_token", [""])[0]
            if not token:
                raise HTTPException(
                    status_code=400, detail="Failed to get the access token"
                )
            return token

    async def get_user_info(self, token: str):
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {token}"},
            )
            user_response.raise_for_status()
            github_user = user_response.json()

            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {token}"},
            )
            emails_response.raise_for_status()
            emails = emails_response.json()

            github_user.update({"emails": emails})
            user = User(
                identifier=github_user["login"],
                metadata={"image": github_user["avatar_url"], "provider": "github"},
            )
            return (github_user, user)


class GoogleOAuthProvider(OAuthProvider):
    id = "google"
    env = ["OAUTH_GOOGLE_CLIENT_ID", "OAUTH_GOOGLE_CLIENT_SECRET"]
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"

    def __init__(self):
        self.client_id = os.environ.get("OAUTH_GOOGLE_CLIENT_ID")
        self.client_secret = os.environ.get("OAUTH_GOOGLE_CLIENT_SECRET")
        self.authorize_params = {
            "scope": "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email",
            "response_type": "code",
            "access_type": "offline",
        }

        if prompt := self.get_prompt():
            self.authorize_params["prompt"] = prompt

    async def get_token(self, code: str, url: str):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": url,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data=payload,
            )
            response.raise_for_status()
            json = response.json()
            token = json.get("access_token")
            if not token:
                raise httpx.HTTPStatusError(
                    "Failed to get the access token",
                    request=response.request,
                    response=response,
                )
            return token

    async def get_user_info(self, token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/userinfo/v2/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            google_user = response.json()
            user = User(
                identifier=google_user["email"],
                metadata={"image": google_user["picture"], "provider": "google"},
            )
            return (google_user, user)




class GenericOAuthProvider(OAuthProvider):
    env = [
        "OAUTH_GENERIC_CLIENT_ID",
        "OAUTH_GENERIC_CLIENT_SECRET",
        "OAUTH_GENERIC_AUTH_URL",
        "OAUTH_GENERIC_TOKEN_URL",
        "OAUTH_GENERIC_USER_INFO_URL",
        "OAUTH_GENERIC_SCOPES",
    ]
    id = os.environ.get("OAUTH_GENERIC_NAME", "generic")

    def __init__(self):
        self.client_id = os.environ.get("OAUTH_GENERIC_CLIENT_ID")
        self.client_secret = os.environ.get("OAUTH_GENERIC_CLIENT_SECRET")
        self.authorize_url = os.environ.get("OAUTH_GENERIC_AUTH_URL")
        self.token_url = os.environ.get("OAUTH_GENERIC_TOKEN_URL")
        self.user_info_url = os.environ.get("OAUTH_GENERIC_USER_INFO_URL")
        self.scopes = os.environ.get("OAUTH_GENERIC_SCOPES")
        self.user_identifier = os.environ.get("OAUTH_GENERIC_USER_IDENTIFIER", "email")

        self.authorize_params = {
            "scope": self.scopes,
            "response_type": "code",
        }

        if prompt := self.get_prompt():
            self.authorize_params["prompt"] = prompt

    async def get_token(self, code: str, url: str):
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": url,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=payload)
            response.raise_for_status()
            json = response.json()
            token = json.get("access_token")
            if not token:
                raise httpx.HTTPStatusError(
                    "Failed to get the access token",
                    request=response.request,
                    response=response,
                )
            return token

    async def get_user_info(self, token: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_url,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            server_user = response.json()
            user = User(
                identifier=server_user.get(self.user_identifier),
                metadata={
                    "provider": self.id,
                },
            )
            return (server_user, user)


providers = [
    GithubOAuthProvider(),
    GoogleOAuthProvider(),
]


def get_oauth_provider(provider: str) -> Optional[OAuthProvider]:
    for p in providers:
        if p.id == provider:
            return p
    return None


def get_configured_oauth_providers():
    return [p.id for p in providers if p.is_configured()]