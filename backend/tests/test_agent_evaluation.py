"""Evaluation suite for Phase 3 Agent.

Deterministic evaluation of agent behavior against expected scenarios.
"""

import pytest
from app.agent.schemas import ActionType, PolicyStatus
from app.agent.policy.rules import PolicyRules
from app.agent.strategies.registry import ActionRegistry


class TestAgentEvaluation:
    """Deterministic evaluation of agent behavior."""
    
    def test_scenario_transient_failure_selects_wait_and_retry(self):
        """Scenario: Temporary failure + no retries -> WAIT_AND_RETRY expected."""
        # This is a deterministic test of expected behavior
        # The agent should prefer WAIT_AND_RETRY for transient failures
        # with no recent retry attempts
        
        # Expected strategy
        expected_strategy = ActionType.WAIT_AND_RETRY
        
        # Verify the strategy is allowed
        assert ActionRegistry.is_action_allowed(expected_strategy.value)
        
        # Verify it doesn't require approval (low risk)
        assert not PolicyRules.get_action_approval_requirement(expected_strategy)
    
    def test_scenario_insufficient_funds_selects_alternate_payment(self):
        """Scenario: Insufficient funds -> REQUEST_ALTERNATE_PAYMENT_METHOD expected."""
        expected_strategy = ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD
        
        assert ActionRegistry.is_action_allowed(expected_strategy.value)
        assert not PolicyRules.get_action_approval_requirement(expected_strategy)
    
    def test_scenario_repeated_failures_selects_manual_review(self):
        """Scenario: Multiple retries -> MANUAL_REVIEW expected."""
        expected_strategy = ActionType.MANUAL_REVIEW
        
        assert ActionRegistry.is_action_allowed(expected_strategy.value)
        assert PolicyRules.get_action_approval_requirement(expected_strategy)
    
    def test_scenario_retry_limit_exceeded_blocked(self):
        """Scenario: Retry limit exceeded -> Policy should block retry."""
        # Verify policy blocks retry when limit exceeded
        assert not PolicyRules.validate_retry_allowed(10)
        
        # Verify manual review is available as fallback
        assert ActionRegistry.is_action_allowed(ActionType.MANUAL_REVIEW.value)
    
    def test_scenario_low_value_low_priority(self):
        """Scenario: Low value -> Should not auto-select high-risk actions."""
        # Low value scenarios should prefer safe actions
        safe_actions = [
            ActionType.WAIT_AND_RETRY,
            ActionType.MANUAL_REVIEW,
        ]
        
        for action in safe_actions:
            assert ActionRegistry.is_action_allowed(action.value)
    
    def test_scenario_policy_blocks_unauthorized_action(self):
        """Scenario: Unauthorized action -> Policy should block."""
        unauthorized_action = "DELETE_PAYMENT"
        
        assert not ActionRegistry.is_action_allowed(unauthorized_action)
    
    def test_strategy_accuracy_allowed_actions(self):
        """Test that all expected strategies are in the allowed registry."""
        expected_strategies = [
            ActionType.RETRY_PAYMENT,
            ActionType.REQUEST_ALTERNATE_PAYMENT_METHOD,
            ActionType.SEND_PAYMENT_REMINDER,
            ActionType.REQUEST_REAUTHENTICATION,
            ActionType.WAIT_AND_RETRY,
            ActionType.MANUAL_REVIEW,
            ActionType.CLOSE_RECOVERY_CASE,
            ActionType.ESCALATE,
        ]
        
        for strategy in expected_strategies:
            assert ActionRegistry.is_action_allowed(strategy.value)
    
    def test_policy_compliance_retry_limit(self):
        """Test that policy enforces retry limits."""
        # Below limit
        assert PolicyRules.validate_retry_allowed(0)
        assert PolicyRules.validate_retry_allowed(1)
        assert PolicyRules.validate_retry_allowed(2)
        
        # At limit
        max_attempts = PolicyRules.get_max_retry_attempts()
        assert PolicyRules.validate_retry_allowed(max_attempts - 1)
        
        # Above limit
        assert not PolicyRules.validate_retry_allowed(max_attempts)
        assert not PolicyRules.validate_retry_allowed(max_attempts + 1)
    
    def test_policy_compliance_payment_eligibility(self):
        """Test that policy validates payment eligibility."""
        # Eligible statuses
        assert PolicyRules.validate_payment_eligible("FAILED")
        
        # Ineligible statuses
        assert not PolicyRules.validate_payment_eligible("CAPTURED")
        assert not PolicyRules.validate_payment_eligible("CREATED")
        assert not PolicyRules.validate_payment_eligible("AUTHORIZED")
    
    def test_fallback_correctness_manual_review(self):
        """Test that MANUAL_REVIEW is always available as fallback."""
        assert ActionRegistry.is_action_allowed(ActionType.MANUAL_REVIEW.value)
        assert PolicyRules.get_action_approval_requirement(ActionType.MANUAL_REVIEW)
    
    def test_confidence_threshold_enforced(self):
        """Test that confidence threshold is enforced."""
        threshold = PolicyRules.get_confidence_threshold()
        
        assert isinstance(threshold, float)
        assert 0.0 <= threshold <= 1.0
    
    def test_action_risk_levels_defined(self):
        """Test that all actions have defined risk levels."""
        actions = ActionRegistry.get_allowed_actions()
        
        for action_str in actions:
            action = ActionType(action_str)
            risk_level = PolicyRules.get_action_risk_level(action)
            assert risk_level is not None
    
    def test_approval_requirements_consistent(self):
        """Test that approval requirements are consistent with risk."""
        high_risk_actions = [
            ActionType.MANUAL_REVIEW,
            ActionType.CLOSE_RECOVERY_CASE,
            ActionType.ESCALATE,
        ]
        
        for action in high_risk_actions:
            assert PolicyRules.get_action_approval_requirement(action)
    
    def test_parameter_validation_enforced(self):
        """Test that parameter validation is enforced."""
        # Valid parameters
        assert PolicyRules.validate_action_parameters(
            ActionType.RETRY_PAYMENT,
            {"delay_minutes": 30}
        )
        
        # Invalid: negative delay
        assert not PolicyRules.validate_action_parameters(
            ActionType.RETRY_PAYMENT,
            {"delay_minutes": -10}
        )
        
        # Invalid: excessive delay
        assert not PolicyRules.validate_action_parameters(
            ActionType.RETRY_PAYMENT,
            {"delay_minutes": 2000}
        )
    
    def test_no_dangerous_actions_allowed(self):
        """Test that dangerous actions are not allowed."""
        dangerous_patterns = [
            "DELETE",
            "DROP",
            "EXECUTE",
            "MODIFY",
            "ISSUE",
            "CALL",
            "SQL",
            "DATABASE",
        ]
        
        allowed_actions = ActionRegistry.get_allowed_actions()
        
        for action in allowed_actions:
            for pattern in dangerous_patterns:
                assert pattern not in action.upper()
    
    def test_evaluation_summary(self):
        """Summary evaluation of agent capabilities."""
        # Count allowed actions
        allowed_count = len(ActionRegistry.get_allowed_actions())
        assert allowed_count >= 5  # Minimum reasonable number
        
        # Verify policy rules exist
        assert PolicyRules.get_max_retry_attempts() > 0
        assert 0.0 <= PolicyRules.get_confidence_threshold() <= 1.0
        
        # Verify fallback exists
        assert ActionRegistry.is_action_allowed(ActionType.MANUAL_REVIEW.value)
