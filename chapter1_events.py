"""第一章事件系统对外入口。

v0.1.26 只初始化事件状态，不接入真实事件池。
"""

from __future__ import annotations

from typing import Any, Dict, List

from chapter1_event_state import ensure_event_state


def initialize_chapter1_events(player: Any) -> None:
    ensure_event_state(player)


def process_chapter1_monthly_events(
    player: Any,
    current_month: int,
    *,
    interactive: bool = True,
    rng: Any = None,
) -> List[Dict[str, Any]]:
    """Return an empty event list until real chapter one events are enabled."""
    del current_month, interactive, rng
    ensure_event_state(player)
    return []


def get_chapter1_event_debug_summary(player: Any) -> Dict[str, Any]:
    ensure_event_state(player)
    return {
        "triggered_event_count": len(getattr(player, "triggered_event_ids", []) or []),
        "active_cooldown_count": len(getattr(player, "event_cooldowns", {}) or {}),
        "monthly_event_log_count": len(getattr(player, "monthly_event_log", []) or []),
        "route_tags": list(getattr(player, "route_tags", []) or []),
        "risk_levels": {
            "theft_trace_level": int(getattr(player, "theft_trace_level", 0)),
            "blackwater_debt": int(getattr(player, "blackwater_debt", 0)),
            "blackwater_trace_level": int(getattr(player, "blackwater_trace_level", 0)),
            "demonic_contamination": int(getattr(player, "demonic_contamination", 0)),
            "pill_toxin_level": int(getattr(player, "pill_toxin_level", 0)),
            "public_scandal_level": int(getattr(player, "public_scandal_level", 0)),
            "field_pollution_level": int(getattr(player, "field_pollution_level", 0)),
            "consumable_dependency_level": int(getattr(player, "consumable_dependency_level", 0)),
            "resource_scatter_level": int(getattr(player, "resource_scatter_level", 0)),
        },
    }
