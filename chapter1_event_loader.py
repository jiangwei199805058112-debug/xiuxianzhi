"""第一章事件配置加载与基础校验。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from event_engine import EventConfigError, load_json_file


CHAPTER1_EVENT_CONFIG_DIR = Path("configs/events/chapter1")
CORE_CONFIG_FILES = {
    "schema": "event_schema.json",
    "monthly_rules": "monthly_rules.json",
    "event_weights": "event_weights.json",
    "route_tags": "routes/route_tags.json",
    "route_detection_rules": "routes/route_detection_rules.json",
}


def _base_dir(base_dir: Path | None = None) -> Path:
    return Path(base_dir) if base_dir is not None else CHAPTER1_EVENT_CONFIG_DIR


def load_chapter1_event_configs(base_dir: Path | None = None) -> Dict[str, Any]:
    root = _base_dir(base_dir)
    configs: Dict[str, Any] = {}
    for key, filename in CORE_CONFIG_FILES.items():
        path = root / filename
        if not path.exists():
            raise EventConfigError(f"Missing config: {path}")
        configs[key] = load_json_file(path)
    validate_chapter1_event_configs(configs)
    return configs


def validate_chapter1_event_configs(configs: Dict[str, Any]) -> None:
    schema = configs.get("schema")
    if not isinstance(schema, dict):
        raise EventConfigError("Invalid config: event_schema.json root must be an object")
    required = schema.get("required_event_fields", [])
    if not isinstance(required, list) or "event_id" not in required:
        raise EventConfigError("Invalid config: event_schema.json missing required_event_fields")

    route_config = configs.get("route_tags")
    if not isinstance(route_config, dict):
        raise EventConfigError("Invalid config: routes/route_tags.json root must be an object")
    route_tags = route_config.get("route_tags", [])
    if not isinstance(route_tags, list) or not all(isinstance(tag, str) and tag for tag in route_tags):
        raise EventConfigError("Invalid config: routes/route_tags.json route_tags must be non-empty strings")

    monthly_rules = configs.get("monthly_rules")
    if not isinstance(monthly_rules, dict):
        raise EventConfigError("Invalid config: monthly_rules.json root must be an object")
    event_weights = configs.get("event_weights")
    if not isinstance(event_weights, dict):
        raise EventConfigError("Invalid config: event_weights.json root must be an object")
    route_detection = configs.get("route_detection_rules")
    if not isinstance(route_detection, dict):
        raise EventConfigError("Invalid config: routes/route_detection_rules.json root must be an object")


def load_chapter1_event_pool(pool_name: str, base_dir: Path | None = None) -> List[Dict[str, Any]]:
    root = _base_dir(base_dir)
    safe_name = str(pool_name).strip()
    if not safe_name:
        return []
    path = root / "pools" / f"{safe_name}.json"
    if not path.exists():
        return []
    data = load_json_file(path)
    if not isinstance(data, list):
        raise EventConfigError(f"Invalid event pool: {path} root must be an array")
    events = [row for row in data if isinstance(row, dict)]
    configs = load_chapter1_event_configs(root)
    validate_chapter1_events(events, configs=configs, source=path)
    return events


def load_chapter1_event_pools(
    pool_names: Iterable[str] | None = None,
    base_dir: Path | None = None,
) -> List[Dict[str, Any]]:
    root = _base_dir(base_dir)
    names = list(pool_names) if pool_names is not None else [
        "farm_events",
        "alchemy_events",
        "mixed_events",
    ]
    configs = load_chapter1_event_configs(root)
    all_events: List[Dict[str, Any]] = []
    for pool_name in names:
        path = root / "pools" / f"{str(pool_name).strip()}.json"
        if not path.exists():
            continue
        data = load_json_file(path)
        if not isinstance(data, list):
            raise EventConfigError(f"Invalid event pool: {path} root must be an array")
        events = [row for row in data if isinstance(row, dict)]
        validate_chapter1_events(events, configs=configs, source=path)
        all_events.extend(events)
    _validate_event_ids(all_events)
    return all_events


def validate_chapter1_events(
    events: List[Dict[str, Any]],
    *,
    configs: Dict[str, Any],
    source: Path | str,
) -> None:
    schema = configs.get("schema", {})
    required_fields = schema.get("required_event_fields", [])
    route_tags = set(configs.get("route_tags", {}).get("route_tags", []))
    for event in events:
        event_id = str(event.get("event_id") or "")
        for field in required_fields:
            if field not in event:
                raise EventConfigError(f"Invalid event {event_id or '<missing>'}: missing {field} in {source}")
        if not event_id:
            raise EventConfigError(f"Invalid event: missing event_id in {source}")
        if not isinstance(event.get("repeatable"), bool):
            raise EventConfigError(f"Invalid event {event_id}: repeatable must be boolean")
        if int(event.get("weight", 0) or 0) < 0:
            raise EventConfigError(f"Invalid event {event_id}: weight must be non-negative")
        if int(event.get("cooldown_months", event.get("cooldown", 0)) or 0) < 0:
            raise EventConfigError(f"Invalid event {event_id}: cooldown must be non-negative")
        month_min = event.get("month_min")
        month_max = event.get("month_max")
        if month_min is not None and month_max is not None and int(month_min) > int(month_max):
            raise EventConfigError(f"Invalid event {event_id}: month_min greater than month_max")
        choices = event.get("choices")
        if not isinstance(choices, list) or not choices:
            raise EventConfigError(f"Invalid event {event_id}: choices must be a non-empty array")
        for choice in choices:
            if not isinstance(choice, dict) or not str(choice.get("choice_id") or ""):
                raise EventConfigError(f"Invalid event {event_id}: choice missing choice_id")
        for tag in event.get("route_tags", []) or []:
            if tag not in route_tags:
                raise EventConfigError(f"Invalid route tag: {tag}")
    _validate_event_ids(events)


def _validate_event_ids(events: List[Dict[str, Any]]) -> None:
    seen: set[str] = set()
    for event in events:
        event_id = str(event.get("event_id") or "")
        if not event_id:
            raise EventConfigError("Invalid event: missing event_id")
        if event_id in seen:
            raise EventConfigError(f"Duplicate event_id: {event_id}")
        seen.add(event_id)
