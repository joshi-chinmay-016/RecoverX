"""Deterministic failure classification for revenue intelligence."""

from typing import Optional
from app.intelligence.schemas import FeatureSet, FailureClassification, FailureCategory


class FailureClassifier:
    """Classify payment failures into normalized categories."""
    
    # Razorpay error code mappings
    RAZORPAY_ERROR_CATEGORIES = {
        # Insufficient funds
        "BAD_REQUEST_ERROR": FailureCategory.PAYMENT_METHOD_FAILURE,
        "INVALID_SIGNATURE": FailureCategory.AUTHENTICATION_FAILURE,
        
        # Bank failures
        "GATEWAY_ERROR": FailureCategory.BANK_FAILURE,
        "BANK_ERROR": FailureCategory.BANK_FAILURE,
        
        # Network failures
        "NETWORK_ERROR": FailureCategory.NETWORK_FAILURE,
        "CONNECTION_ERROR": FailureCategory.NETWORK_FAILURE,
        
        # Authentication
        "AUTHENTICATION_ERROR": FailureCategory.AUTHENTICATION_FAILURE,
        "AUTHORIZATION_ERROR": FailureCategory.AUTHENTICATION_FAILURE,
        
        # Limits
        "LIMIT_ERROR": FailureCategory.LIMIT_EXCEEDED,
        
        # Temporary
        "TIMEOUT_ERROR": FailureCategory.TEMPORARY_FAILURE,
        "SERVER_ERROR": FailureCategory.TEMPORARY_FAILURE,
    }
    
    # Failure message patterns
    FAILURE_MESSAGE_PATTERNS = {
        "insufficient": FailureCategory.INSUFFICIENT_FUNDS,
        "balance": FailureCategory.INSUFFICIENT_FUNDS,
        "funds": FailureCategory.INSUFFICIENT_FUNDS,
        "bank": FailureCategory.BANK_FAILURE,
        "network": FailureCategory.NETWORK_FAILURE,
        "timeout": FailureCategory.TEMPORARY_FAILURE,
        "temporary": FailureCategory.TEMPORARY_FAILURE,
        "auth": FailureCategory.AUTHENTICATION_FAILURE,
        "limit": FailureCategory.LIMIT_EXCEEDED,
        "method": FailureCategory.PAYMENT_METHOD_FAILURE,
    }
    
    def classify(self, features: FeatureSet) -> FailureClassification:
        """Classify a payment failure based on features."""
        failure_code = features.failure_code or ""
        failure_message = features.failure_message or ""
        payment_method = features.payment_method or ""
        
        # Try to classify by message first (for high-specificity patterns like insufficient funds, timeout)
        category = self._classify_by_message(failure_message)
        
        # If unknown, try by error code
        if category == FailureCategory.UNKNOWN:
            category = self._classify_by_error_code(failure_code)
        
        # If still unknown, try by payment method
        if category == FailureCategory.UNKNOWN:
            category = self._classify_by_payment_method(payment_method, failure_message)
        
        # Generate normalized reason
        normalized_reason = self._generate_normalized_reason(category, failure_code, failure_message)
        
        # Generate explanation
        explanation = self._generate_explanation(category, features)
        
        # Calculate confidence based on classification method
        confidence = self._calculate_confidence(category, failure_code, failure_message)
        
        return FailureClassification(
            category=category,
            normalized_reason=normalized_reason,
            confidence=confidence,
            explanation=explanation,
        )
    
    def _classify_by_error_code(self, error_code: str) -> FailureCategory:
        """Classify based on Razorpay error code."""
        if not error_code:
            return FailureCategory.UNKNOWN
        
        error_code_upper = error_code.upper()
        
        for pattern, category in self.RAZORPAY_ERROR_CATEGORIES.items():
            if pattern in error_code_upper:
                return category
        
        return FailureCategory.UNKNOWN
    
    def _classify_by_message(self, message: str) -> FailureCategory:
        """Classify based on failure message."""
        if not message:
            return FailureCategory.UNKNOWN
        
        message_lower = message.lower()
        
        for pattern, category in self.FAILURE_MESSAGE_PATTERNS.items():
            if pattern in message_lower:
                return category
        
        return FailureCategory.UNKNOWN
    
    def _classify_by_payment_method(self, payment_method: str, message: str) -> FailureCategory:
        """Classify based on payment method and message."""
        if not payment_method:
            return FailureCategory.UNKNOWN
        
        # UPI-specific failures
        if "upi" in payment_method.lower():
            if "timeout" in message.lower() or "network" in message.lower():
                return FailureCategory.NETWORK_FAILURE
            return FailureCategory.PAYMENT_METHOD_FAILURE
        
        # Card-specific failures
        if "card" in payment_method.lower():
            if "insufficient" in message.lower():
                return FailureCategory.INSUFFICIENT_FUNDS
            if any(k in message.lower() for k in ["declined", "expired", "invalid card", "cvv", "card"]):
                return FailureCategory.PAYMENT_METHOD_FAILURE
            return FailureCategory.UNKNOWN
        
        # Netbanking-specific failures
        if "netbanking" in payment_method.lower():
            if "bank" in message.lower():
                return FailureCategory.BANK_FAILURE
            return FailureCategory.PAYMENT_METHOD_FAILURE
        
        return FailureCategory.UNKNOWN
    
    def _generate_normalized_reason(self, category: FailureCategory, error_code: str, message: str) -> str:
        """Generate a normalized reason string."""
        reasons = {
            FailureCategory.INSUFFICIENT_FUNDS: "Insufficient funds in customer account",
            FailureCategory.BANK_FAILURE: "Bank processing failure",
            FailureCategory.NETWORK_FAILURE: "Network connectivity issue",
            FailureCategory.AUTHENTICATION_FAILURE: "Authentication or authorization failed",
            FailureCategory.LIMIT_EXCEEDED: "Transaction limit exceeded",
            FailureCategory.TEMPORARY_FAILURE: "Temporary system failure",
            FailureCategory.PAYMENT_METHOD_FAILURE: "Payment method processing error",
            FailureCategory.UNKNOWN: "Unknown failure reason",
        }
        
        base_reason = reasons.get(category, "Unknown failure reason")
        
        # Append error code if available
        if error_code:
            return f"{base_reason} (Error: {error_code})"
        
        return base_reason
    
    def _generate_explanation(self, category: FailureCategory, features: FeatureSet) -> str:
        """Generate a human-readable explanation."""
        retry_count = features.retry_count
        
        explanations = {
            FailureCategory.INSUFFICIENT_FUNDS: f"Payment failed due to insufficient funds after {retry_count} attempt(s).",
            FailureCategory.BANK_FAILURE: f"Payment failed due to bank processing error after {retry_count} attempt(s).",
            FailureCategory.NETWORK_FAILURE: f"Payment failed due to network connectivity issue after {retry_count} attempt(s).",
            FailureCategory.AUTHENTICATION_FAILURE: f"Payment failed due to authentication issue after {retry_count} attempt(s).",
            FailureCategory.LIMIT_EXCEEDED: f"Payment failed due to transaction limit being exceeded after {retry_count} attempt(s).",
            FailureCategory.TEMPORARY_FAILURE: f"Payment failed due to temporary system issue after {retry_count} attempt(s).",
            FailureCategory.PAYMENT_METHOD_FAILURE: f"Payment failed due to payment method error after {retry_count} attempt(s).",
            FailureCategory.UNKNOWN: f"Payment failed for unknown reasons after {retry_count} attempt(s).",
        }
        
        return explanations.get(category, f"Payment failed after {retry_count} attempt(s).")
    
    def _calculate_confidence(self, category: FailureCategory, error_code: str, message: str) -> float:
        """Calculate confidence in classification."""
        # High confidence if we have a matching error code
        if error_code and category != FailureCategory.UNKNOWN:
            return 0.9
        
        # Medium confidence if we have a matching message pattern
        if message and category != FailureCategory.UNKNOWN:
            return 0.7
        
        # Low confidence for unknown classification
        if category == FailureCategory.UNKNOWN:
            return 0.3
        
        # Default medium confidence
        return 0.6
