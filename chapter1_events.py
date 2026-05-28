"""第一章事件系统对外入口。"""

from __future__ import annotations

import random
from typing import Any, Dict, List

from chapter1_event_loader import load_chapter1_event_configs, load_chapter1_event_pools
from chapter1_event_state import ensure_event_state, reset_monthly_action_counts
from event_engine import apply_event_choice, is_event_available, select_event, tick_event_cooldowns


CHAPTER1_MVP_EVENT_POOLS = (
    "farm_events",
    "alchemy_events",
    "mixed_events",
    "theft_events",
    "blackwater_events",
    "market_events",
)


def initialize_chapter1_events(player: Any) -> None:
    ensure_event_state(player)


def process_chapter1_monthly_events(
    player: Any,
    current_month: int,
    *,
    interactive: bool = True,
    rng: Any = None,
    force: bool = False,
) -> List[Dict[str, Any]]:
    """Process at most one low-risk chapter one MVP event for this month."""
    del interactive
    ensure_event_state(player)
    random_source = rng or random
    logs: List[Dict[str, Any]] = []
    try:
        tick_event_cooldowns(player)
        configs = load_chapter1_event_configs()
        monthly_rules = configs.get("monthly_rules", {})
        if not bool(monthly_rules.get("enabled", False)):
            return logs
        if not force:
            trigger_chance = float(monthly_rules.get("monthly_trigger_chance", 0.0) or 0.0)
            if random_source.random() > trigger_chance:
                return logs
        candidates = [
            event
            for event in load_chapter1_event_pools(CHAPTER1_MVP_EVENT_POOLS)
            if is_event_available(player, event, current_month)
        ]
        event = select_event(candidates, random_source)
        if not event:
            return logs
        choice_id = str(event.get("auto_choice") or "")
        if not choice_id:
            choices = event.get("choices", [])
            choice_id = str(choices[0].get("choice_id")) if choices else ""
        if not choice_id:
            return logs
        choice = apply_event_choice(player, event, choice_id)
        log_entry = _build_event_log_entry(event, choice, current_month)
        player.monthly_event_log.append(log_entry)
        logs.append(log_entry)
        return logs
    finally:
        reset_monthly_action_counts(player)


def _build_event_log_entry(event: Dict[str, Any], choice: Dict[str, Any], current_month: int) -> Dict[str, Any]:
    return {
        "month": int(current_month),
        "event_id": str(event.get("event_id") or ""),
        "title": str(event.get("title") or ""),
        "event_type": str(event.get("event_type") or ""),
        "risk_level": str(event.get("risk_level") or ""),
        "route_tags": list(event.get("route_tags") or []),
        "choice_id": str(choice.get("choice_id") or ""),
        "choice_label": str(choice.get("label") or ""),
        "text": str(event.get("text") or ""),
        "effect_summary": _effect_summary(choice.get("effects", [])),
    }


def _effect_summary(effects: Any) -> str:
    if not effects:
        return "无额外变化"
    if isinstance(effects, dict):
        effects = [effects]
    rows: List[str] = []
    for effect in effects:
        if not isinstance(effect, dict):
            continue
        summary = str(effect.get("summary") or "")
        if summary:
            rows.append(summary)
            continue
        field = str(effect.get("field") or effect.get("attr") or "")
        op = str(effect.get("op") or effect.get("operator") or "")
        value = effect.get("value")
        if field:
            rows.append(f"{field} {op} {value}")
    return "；".join(rows) if rows else "无额外变化"


def format_chapter1_event_log(log_entry: Dict[str, Any]) -> str:
    lines = [
        f"第一章事件：{log_entry.get('title', '')}",
        str(log_entry.get("text", "")),
        f"选择：{log_entry.get('choice_label', '')}",
        f"结果：{log_entry.get('effect_summary', '无额外变化')}",
    ]
    return "\n".join(line for line in lines if line)


def get_chapter1_event_debug_summary(player: Any) -> Dict[str, Any]:
    ensure_event_state(player)
    return {
        "triggered_event_count": len(getattr(player, "triggered_event_ids", []) or []),
        "active_cooldown_count": len(getattr(player, "event_cooldowns", {}) or {}),
        "monthly_event_log_count": len(getattr(player, "monthly_event_log", []) or []),
        "monthly_action_counts": dict(getattr(player, "monthly_action_counts", {}) or {}),
        "route_tags": list(getattr(player, "route_tags", []) or []),
        "risk_levels": {
            "theft_trace_level": int(getattr(player, "theft_trace_level", 0)),
            "theft_suspicion_level": int(getattr(player, "theft_suspicion_level", 0)),
            "blackwater_debt": int(getattr(player, "blackwater_debt", 0)),
            "blackwater_trace_level": int(getattr(player, "blackwater_trace_level", 0)),
            "market_dependency_level": int(getattr(player, "market_dependency_level", 0)),
            "talisman_failure_risk": int(getattr(player, "talisman_failure_risk", 0)),
            "demonic_contamination": int(getattr(player, "demonic_contamination", 0)),
            "pill_toxin_level": int(getattr(player, "pill_toxin_level", 0)),
            "public_scandal_level": int(getattr(player, "public_scandal_level", 0)),
            "field_pollution_level": int(getattr(player, "field_pollution_level", 0)),
            "consumable_dependency_level": int(getattr(player, "consumable_dependency_level", 0)),
            "resource_scatter_level": int(getattr(player, "resource_scatter_level", 0)),
        },
    }
