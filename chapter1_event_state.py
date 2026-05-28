"""第一章事件状态默认值与旧存档补字段。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


EVENT_STATE_DEFAULTS: Dict[str, Any] = {
    "triggered_event_ids": [],
    "event_cooldowns": {},
    "monthly_event_log": [],
    "monthly_action_counts": {},
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
    "monthly_action_counts",
}
EVENT_INT_FIELDS = {
    key
    for key, value in EVENT_STATE_DEFAULTS.items()
    if isinstance(value, int)
}
SYSTEM_CONTACT_GROUPS = {
    "farm_care": "farming",
    "farm_tend": "farming",
    "farm_harvest": "farming",
    "herb_gathering": "farming",
    "alchemy": "alchemy",
    "meditation": "orthodox",
    "combat_training": "orthodox",
    "market": "market",
    "blackwater": "blackwater",
    "social": "social",
    "intel": "social",
    "theft": "theft",
    "demonic": "demonic",
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

    action_counts = getattr(player, "monthly_action_counts", {}) or {}
    if not isinstance(action_counts, dict):
        action_counts = {}
    player.monthly_action_counts = {
        str(action): max(0, _safe_int(count))
        for action, count in action_counts.items()
        if str(action) and _safe_int(count) > 0
    }
    _refresh_system_contacts(player)

    for key in EVENT_INT_FIELDS:
        setattr(player, key, max(0, _safe_int(getattr(player, key, 0))))


def _refresh_system_contacts(player: Any) -> None:
    counts = getattr(player, "monthly_action_counts", {}) or {}
    active = {
        SYSTEM_CONTACT_GROUPS.get(key, key)
        for key, value in counts.items()
        if key != "system_contacts" and _safe_int(value) > 0
    }
    if active:
        counts["system_contacts"] = len(active)
    else:
        counts.pop("system_contacts", None)
    player.monthly_action_counts = counts


def record_monthly_action(player: Any, action_key: str, amount: int = 1) -> None:
    ensure_event_state(player)
    key = str(action_key)
    if not key:
        return
    counts = dict(getattr(player, "monthly_action_counts", {}) or {})
    counts[key] = max(0, _safe_int(counts.get(key, 0)) + max(0, _safe_int(amount, 1)))
    player.monthly_action_counts = counts
    _refresh_system_contacts(player)


def reset_monthly_action_counts(player: Any) -> None:
    player.monthly_action_counts = {}
