"""Tool: Get allowed actions for agent reasoning."""

from typing import Dict, Any, List
from app.agent.strategies.registry import ActionRegistry, ActionType


def get_allowed_actions(context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get list and metadata of all allowed recovery actions (read-only)."""
    allowed_list = ActionRegistry.get_allowed_actions()
    actions_detail = []
    
    for action_type in ActionType:
        cfg = ActionRegistry.get_action_config(action_type)
        actions_detail.append({
            "name": action_type.value,
            "description": cfg.get("description", ""),
            "risk_level": cfg.get("risk_level", "LOW"),
            "requires_approval": cfg.get("requires_approval", False),
            "parameters": cfg.get("parameters", {}),
        })

    return {
        "allowed_actions": allowed_list,
        "actions_detail": actions_detail,
        "total_allowed": len(allowed_list),
    }
