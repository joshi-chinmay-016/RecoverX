import hmac
import hashlib
from app.core.logging import get_logger

logger = get_logger(__name__)


def verify_webhook_signature(
    raw_body: bytes, signature: str, webhook_secret: str
) -> bool:
    """
    Verify Razorpay webhook signature using HMAC SHA256.
    
    IMPORTANT: This must use the raw HTTP request body, not a re-serialized JSON.
    """
    expected_signature = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)
