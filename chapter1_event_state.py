"""第一章事件状态默认值与旧存档补字段。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


EVENT_STATE_DEFAULTS: Dict[str, Any] = {
    "triggered_event_ids": [],
    "event_cooldowns": {},
    "monthly_event_log": [],
    "route_tags": [],
    "theft_trace_level": 0,
    "blackwater_debt": 0,
    "blackwater_trace_level": 0,
    "demonic_contamination": 0,
    "pill_toxin_level": 0,
    "public_scandal_level": 0,
    "field_pollution_level": 0,
    "consumable_dependency_level": 0,
    "resource_scatter_level": 0,
    "orthodox_path_level": 0,
    "farming_path_level": 0,
    "alchemy_path_level": 0,
    "theft_path_level": 0,
    "blackwater_path_level": 0,
    "intel_social_path_level": 0,
    "demonic_path_level": 0,
    "market_talisman_path_level": 0,
    "mixed_path_score": 0,
}

EVENT_LIST_FIELDS = {
    "triggered_event_ids",
    "monthly_event_log",
    "route_tags",
}
EVENT_DICT_FIELDS = {
    "event_cooldowns",
}
EVENT_INT_FIELDS = {
    key
    for key, value in EVENT_STATE_DEFAULTS.items()
    if isinstance(value, int)
}


def default_event_state_value(key: str) -> Any:
    """Return a fresh default value for mutable event state fields."""
    return deepcopy(EVENT_STATE_DEFAULTS[key])


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ensure_event_state(player: Any) -> None:
    """Backfill and normalize event state on Player-like objects."""
    for key in EVENT_STATE_DEFAULTS:
        if not hasattr(player, key):
            setattr(player, key, default_event_state_value(key))

    player.triggered_event_ids = [
        str(event_id) for event_id in list(getattr(player, "triggered_event_ids", []) or []) if str(event_id)
    ]
    player.monthly_event_log = [
        dict(item) for item in list(getattr(player, "monthly_event_log", []) or []) if isinstance(item, dict)
    ]
    player.route_tags = [
        str(tag) for tag in list(getattr(player, "route_tags", []) or []) if str(tag)
    ]

    cooldowns = getattr(player, "event_cooldowns", {}) or {}
    if not isinstance(cooldowns, dict):
        cooldowns = {}
    player.event_cooldowns = {
        str(event_id): max(0, _safe_int(months_left))
        for event_id, months_left in cooldowns.items()
        if str(event_id) and _safe_int(months_left) > 0
    }

    for key in EVENT_INT_FIELDS:
        setattr(player, key, max(0, _safe_int(getattr(player, key, 0))))
