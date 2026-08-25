"""Prompt Builder for Phase 3 Agent.

Constructs prompts with injection defense and clear boundaries.
"""

from app.agent.prompts.system import get_system_prompt
from app.agent.prompts.recovery import build_recovery_prompt

__all__ = ["get_system_prompt", "build_recovery_prompt"]
