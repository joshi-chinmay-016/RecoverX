import hmac
import hashlib
from typing import Tuple
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.logging import logger


class WebhookVerifier:
    """Verifies Razorpay webhook signatures using HMAC-SHA256."""
    
    @staticmethod
    def verify_signature(raw_body: bytes, signature: str) -> bool:
        """
        Verify webhook signature against raw body.
        
        IMPORTANT: Must use raw bytes, not re-serialized JSON.
        """
        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                settings.razorpay_webhook_secret.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison to prevent timing attacks
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"signature_verification_failed error={str(e)}")
            return False
    
    @staticmethod
    async def extract_and_verify(request: Request) -> Tuple[bytes, str]:
        """
        Extract raw body and signature from request, then verify.
        Returns (raw_body, signature)
        """
        # Read raw body before JSON parsing
        raw_body = await request.body()
        
        # Extract signature header
        signature = request.headers.get("x-razorpay-signature")
        if not signature:
            logger.warning("webhook_missing_signature path=%s body_bytes=%d", request.url.path, len(raw_body))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing signature header"
            )
        
        # Verify signature
        if not WebhookVerifier.verify_signature(raw_body, signature):
            secret_len = len(settings.razorpay_webhook_secret) if settings.razorpay_webhook_secret else 0
            logger.warning(
                "webhook_invalid_signature path=%s body_bytes=%d secret_configured_len=%d signature_prefix=%s",
                request.url.path,
                len(raw_body),
                secret_len,
                signature[:8] if signature else "none"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
        
        logger.info("webhook_signature_verified path=%s body_bytes=%d", request.url.path, len(raw_body))
        return raw_body, signature