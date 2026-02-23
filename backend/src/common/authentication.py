import os
import re
import hashlib
import time
import logging
from datetime import datetime, timezone, timedelta

from joserfc.jwt import JWTClaimsRegistry
from joserfc import jwt
from joserfc.jwk import OctKey
from joserfc.errors import ExpiredTokenError, BadSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException
from src.log_management.generate_error_logs import log_message


class Auth:
    hasher = CryptContext(schemes=["bcrypt"])

    def __init__(self):
        # 🔐 Always use fixed secret from .env
        raw_secret = os.getenv("AUTH_SECRET")

        if not raw_secret:
            log_message("AUTH_SECRET is not set in environment variables", logging.CRITICAL)
            raise RuntimeError("AUTH_SECRET is not set in environment variables")

        # Convert to OctKey (required for HS256 in joserfc)
        self.secret = OctKey.import_key(raw_secret.encode("utf-8"))
        log_message("Auth class initialized successfully", logging.INFO)

    # 🔑 Password Hashing
    def encode_psswrd(self, psswrd, salt):
        encoded_psswrd = psswrd.encode()
        digest = hashlib.pbkdf2_hmac("sha512", encoded_psswrd, salt, 10000)
        return digest.hex()

    # 🎫 Generate JWT
    def encode_token(self, userid):
        try:
            claims = {
                "sub": str(userid),
                "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
                "iat": datetime.now(timezone.utc),
                "scope": "access_token",
            }

            headers = {"alg": "HS256"}

            token = jwt.encode(headers, claims, self.secret)
            log_message(f"JWT token generated for user {userid}", logging.INFO)
            return token
        except Exception as e:
            log_message(f"Failed to generate JWT token: {str(e)}", logging.ERROR)
            raise

    # 🔍 Validate JWT
    def decode_token(self, token):
        try:
            if not re.match(r"^[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+$", token):
                log_message("Invalid token format detected", logging.WARNING)
                raise HTTPException(status_code=401, detail="Invalid token format")

            decoded_token = jwt.decode(token, self.secret)

            registry = JWTClaimsRegistry(now=int(time.time()))
            registry.validate(decoded_token.claims)

            if decoded_token.claims.get("scope") != "access_token":
                log_message("Invalid token scope detected", logging.WARNING)
                raise HTTPException(status_code=401, detail="Invalid token scope")

            log_message(f"Token decoded successfully for user {decoded_token.claims['sub']}", logging.INFO)
            return decoded_token.claims["sub"]

        except ExpiredTokenError:
            log_message("Token has expired", logging.WARNING)
            raise HTTPException(status_code=401, detail="Token has expired")

        except BadSignatureError:
            log_message("Invalid token signature detected", logging.WARNING)
            raise HTTPException(status_code=401, detail="Invalid token signature")

        except Exception as e:
            log_message(f"JWT Decode Error: {type(e).__name__} - {str(e)}", logging.ERROR)
            raise HTTPException(status_code=401, detail="Invalid token")