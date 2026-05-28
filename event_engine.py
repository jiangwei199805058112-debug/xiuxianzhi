"""通用事件引擎骨架。

v0.1.27 提供配置加载、条件判断和效果应用的基础能力。
真实事件触发由第一章事件入口按配置控制。
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class EventConfigError(Exception):
    """Raised when event configuration is missing or malformed."""


def load_json_file(path: str | Path) -> Any:
    config_path = Path(path)
    if not config_path.exists():
        raise EventConfigError(f"Missing config: {config_path}")
    try:
        with config_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as exc:
        raise EventConfigError(f"Invalid JSON: {config_path}: {exc}") from exc


def _get_attr(player: Any, field: str) -> Any:
    if "." in field:
        current: Any = player
        for part in field.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
            if current is None:
                return None
        return current
    if isinstance(player, dict):
        return player.get(field)
    return getattr(player, field, None)


def _has_attr(player: Any, field: str) -> bool:
    if "." in field:
        marker = object()
        current: Any = player
        for part in field.split("."):
            if isinstance(current, dict):
                current = current.get(part, marker)
            else:
                current = getattr(current, part, marker)
            if current is marker:
                return False
        return True
    if isinstance(player, dict):
        return field in player
    return hasattr(player, field)


def check_event_condition(player: Any, condition: Any) -> bool:
    """Check one condition or a list of conditions against player state."""
    if not condition:
        return True
    if isinstance(condition, list):
        return all(check_event_condition(player, item) for item in condition)
    if not isinstance(condition, dict):
        return False
    if "all" in condition:
        return all(check_event_condition(player, item) for item in condition.get("all") or [])
    if "any" in condition:
        return any(check_event_condition(player, item) for item in condition.get("any") or [])

    field = str(condition.get("field") or condition.get("attr") or "")
    op = str(condition.get("op") or condition.get("operator") or "==")
    expected = condition.get("value")
    exists = bool(field) and _has_attr(player, field)
    actual = _get_attr(player, field)

    if op == "exists":
        return exists
    if op == "not_exists":
        return not exists
    if not field:
        return False
    if op == "==":
        return actual == expected
    if op == "!=":
        return actual != expected
    if op in {">", ">=", "<", "<="}:
        try:
            left = float(actual)
            right = float(expected)
        except (TypeError, ValueError):
            return False
        if op == ">":
            return left > right
        if op == ">=":
            return left >= right
        if op == "<":
            return left < right
        return left <= right
    if op == "in":
        return actual in (expected or [])
    if op == "not_in":
        return actual not in (expected or [])
    if op == "contains":
        return expected in (actual or [])
    if op == "not_contains":
        return expected not in (actual or [])
    return False


def _set_attr(player: Any, field: str, value: Any) -> None:
    if "." in field:
        parts = field.split(".")
        current: Any = player
        for part in parts[:-1]:
            if isinstance(current, dict):
                current = current.setdefault(part, {})
            else:
                nested = getattr(current, part, None)
                if nested is None:
                    nested = {}
                    setattr(current, part, nested)
                current = nested
        if isinstance(current, dict):
            current[parts[-1]] = value
        else:
            setattr(current, parts[-1], value)
        return
    if isinstance(player, dict):
        player[field] = value
    else:
        setattr(player, field, value)


def apply_event_effect(player: Any, effect: Any) -> None:
    """Apply a reserved event effect format to player state."""
    if not effect:
        return
    if isinstance(effect, list):
        for item in effect:
            apply_event_effect(player, item)
        return
    if not isinstance(effect, dict):
        return

    field = str(effect.get("field") or effect.get("attr") or "")
    op = str(effect.get("op") or effect.get("operator") or "add")
    value = effect.get("value")
    if not field:
        return

    current = _get_attr(player, field)
    if op == "set":
        _set_attr(player, field, value)
    elif op == "add":
        _set_attr(player, field, int(current or 0) + int(value or 0))
    elif op == "min":
        _set_attr(player, field, min(int(current or 0), int(value or 0)))
    elif op == "max":
        _set_attr(player, field, max(int(current or 0), int(value or 0)))
    elif op == "append":
        rows = list(current or [])
        if value not in rows:
            rows.append(value)
        _set_attr(player, field, rows)
    elif op == "remove":
        rows = [item for item in list(current or []) if item != value]
        _set_attr(player, field, rows)
    elif op == "flag_on":
        rows = list(current or [])
        flag = value if value is not None else field
        if flag not in rows:
            rows.append(flag)
        _set_attr(player, field, rows)
    elif op == "flag_off":
        flag = value if value is not None else field
        rows = [item for item in list(current or []) if item != flag]
        _set_attr(player, field, rows)
    # Other operators are reserved by schema and intentionally left inert.


def is_event_available(player: Any, event: Dict[str, Any], current_month: int) -> bool:
    if not event:
        return False
    event_id = str(event.get("event_id") or "")
    if not event_id:
        return False
    triggered = set(getattr(player, "triggered_event_ids", []) or [])
    if not bool(event.get("repeatable", False)) and event_id in triggered:
        return False
    cooldowns = getattr(player, "event_cooldowns", {}) or {}
    if int(cooldowns.get(event_id, 0) or 0) > 0:
        return False
    month_min = event.get("month_min")
    month_max = event.get("month_max")
    if month_min is not None and current_month < int(month_min):
        return False
    if month_max is not None and current_month > int(month_max):
        return False
    return check_event_condition(player, event.get("conditions", []))


def select_event(candidates: Iterable[Dict[str, Any]], rng: Optional[random.Random] = None) -> Optional[Dict[str, Any]]:
    rows = [event for event in candidates if isinstance(event, dict)]
    if not rows:
        return None
    random_source = rng or random
    weighted: List[tuple[Dict[str, Any], int]] = []
    for event in rows:
        try:
            weight = max(0, int(event.get("weight", 1)))
        except (TypeError, ValueError):
            weight = 1
        if weight:
            weighted.append((event, weight))
    if not weighted:
        return None
    total = sum(weight for _, weight in weighted)
    roll = random_source.uniform(0, total)
    cursor = 0.0
    for event, weight in weighted:
        cursor += weight
        if roll <= cursor:
            return event
    return weighted[-1][0]


def apply_event_choice(player: Any, event: Dict[str, Any], choice_id: str) -> Dict[str, Any]:
    choices = event.get("choices", []) if isinstance(event, dict) else []
    choice = next((row for row in choices if str(row.get("choice_id")) == str(choice_id)), None)
    if not choice:
        raise EventConfigError(f"Missing event choice: {event.get('event_id', '')}:{choice_id}")
    apply_event_effect(player, choice.get("effects", []))
    event_id = str(event.get("event_id") or "")
    if event_id:
        triggered = list(getattr(player, "triggered_event_ids", []) or [])
        if event_id not in triggered:
            triggered.append(event_id)
        setattr(player, "triggered_event_ids", triggered)
        cooldown = int(event.get("cooldown_months", event.get("cooldown", 0)) or 0)
        if cooldown > 0:
            cooldowns = dict(getattr(player, "event_cooldowns", {}) or {})
            cooldowns[event_id] = cooldown
            setattr(player, "event_cooldowns", cooldowns)
    if hasattr(player, "clamp"):
        player.clamp()
    return choice


def tick_event_cooldowns(player: Any) -> None:
    cooldowns = dict(getattr(player, "event_cooldowns", {}) or {})
    next_cooldowns = {}
    for event_id, months_left in cooldowns.items():
        try:
            remaining = int(months_left)
        except (TypeError, ValueError):
            continue
        if remaining > 1:
            next_cooldowns[str(event_id)] = remaining - 1
    setattr(player, "event_cooldowns", next_cooldowns)
