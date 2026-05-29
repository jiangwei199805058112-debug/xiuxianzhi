"""试玩行为记录、月度总结与结局分析。"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List

from cultivation_assets import (
    current_furnace,
    equipment_count,
    equipment_score,
    material_total,
)


ACTION_LOG_LIMIT = 120
MONTHLY_SUMMARY_LIMIT = 24
PLAYTEST_NOTES_LIMIT = 80

ACTION_TYPE_ALIASES = {
    "combat_training": "spell_training",
    "farm_care": "farm",
    "farm_tend": "farm",
    "farm_harvest": "farm",
    "talisman": "market",
    "intel": "social",
}

ACTION_TYPE_LABELS = {
    "meditation": "打坐/静心",
    "herb_gathering": "采药",
    "alchemy": "炼丹",
    "market": "普通坊市",
    "blackwater": "黑水坊市",
    "theft": "盗术",
    "demonic": "魔道",
    "farm": "灵田",
    "equipment": "装备",
    "social": "结交/人情",
    "spell_training": "法术训练",
    "event_choice": "事件选择",
    "preparation": "修炼准备",
    "insight": "突破感悟",
    "save": "存档",
    "unknown": "其他",
}

FIELD_LABELS = {
    "realm_level": "境界层数",
    "cultivation_progress": "修炼进度",
    "cultivation": "修为",
    "physique": "体魄",
    "comprehension": "悟性",
    "combat_exp": "斗法经验",
    "hp": "气血",
    "mp": "灵力",
    "attack": "攻击",
    "defense": "防御",
    "speed": "身法",
    "divine_sense": "神识",
    "luck": "气运",
    "charm": "魅力",
    "dao_heart": "道心",
    "intelligence": "情报值",
    "herbs": "普通灵草",
    "aged_herbs_10": "十年份灵草",
    "aged_herbs_30": "三十年份灵草",
    "spirit_stones": "灵石",
    "pills": "丹药",
    "contribution": "家族贡献",
    "exposure": "暴露度",
    "heart_demon": "心魔值",
    "demonic_qi": "魔气值",
    "karma": "业力值",
    "tracking_marks": "追踪标记",
    "theft_trace_level": "盗术痕迹",
    "theft_suspicion_level": "盗术嫌疑",
    "blackwater_debt": "黑水暗债",
    "blackwater_trace_level": "黑水追踪",
    "meditation_fatigue": "冥坐疲劳",
    "closed_training_months": "闭关月数",
    "cultivation_pressure": "修行缺口",
    "foundation": "根基",
    "mixed_practice_points": "多线点数",
    "adaptive_experience": "临场适应",
    "equipment_count": "装备数量",
    "equipment_score": "装备评分",
    "alchemy_material_total": "炼丹材料",
}

SNAPSHOT_FIELDS = (
    "realm_level",
    "cultivation_progress",
    "cultivation",
    "physique",
    "comprehension",
    "combat_exp",
    "hp",
    "mp",
    "attack",
    "defense",
    "speed",
    "divine_sense",
    "luck",
    "charm",
    "dao_heart",
    "intelligence",
    "herbs",
    "aged_herbs_10",
    "aged_herbs_30",
    "spirit_stones",
    "pills",
    "contribution",
    "exposure",
    "heart_demon",
    "demonic_qi",
    "karma",
    "tracking_marks",
    "theft_trace_level",
    "theft_suspicion_level",
    "blackwater_debt",
    "blackwater_trace_level",
    "meditation_fatigue",
    "closed_training_months",
    "cultivation_pressure",
    "foundation",
    "mixed_practice_points",
    "adaptive_experience",
)

RESOURCE_FIELDS = (
    "spirit_stones",
    "herbs",
    "aged_herbs_10",
    "aged_herbs_30",
    "pills",
    "contribution",
)

RISK_FIELDS = (
    "exposure",
    "heart_demon",
    "demonic_qi",
    "karma",
    "tracking_marks",
    "theft_trace_level",
    "theft_suspicion_level",
    "blackwater_debt",
    "blackwater_trace_level",
    "meditation_fatigue",
    "cultivation_pressure",
)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_list(value: Any) -> List[Any]:
    if not isinstance(value, list):
        return []
    return list(value)


def _clean_int_mapping(value: Any) -> Dict[str, int]:
    if not isinstance(value, dict):
        return {}
    cleaned: Dict[str, int] = {}
    for key, raw_count in value.items():
        count = _safe_int(raw_count)
        if count:
            cleaned[str(key)] = count
    return cleaned


def _clean_str_mapping(value: Any) -> Dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(raw_value) for key, raw_value in value.items() if str(raw_value)}


def ensure_playtest_state(player: Any) -> None:
    """Backfill and normalize playtest log fields for old saves."""
    if not isinstance(getattr(player, "action_log", None), list):
        player.action_log = []
    if not isinstance(getattr(player, "monthly_summary_log", None), list):
        player.monthly_summary_log = []
    if not isinstance(getattr(player, "playtest_notes", None), list):
        player.playtest_notes = []

    player.action_log = [
        dict(entry)
        for entry in _safe_list(getattr(player, "action_log", []))
        if isinstance(entry, dict)
    ][-ACTION_LOG_LIMIT:]
    player.monthly_summary_log = [
        dict(entry)
        for entry in _safe_list(getattr(player, "monthly_summary_log", []))
        if isinstance(entry, dict)
    ][-MONTHLY_SUMMARY_LIMIT:]
    player.playtest_notes = [
        str(note)
        for note in _safe_list(getattr(player, "playtest_notes", []))
        if str(note)
    ][-PLAYTEST_NOTES_LIMIT:]


def normalize_action_type(action_type: str) -> str:
    normalized = str(action_type or "unknown")
    return ACTION_TYPE_ALIASES.get(normalized, normalized)


def action_type_label(action_type: str) -> str:
    return ACTION_TYPE_LABELS.get(normalize_action_type(action_type), str(action_type or "其他"))


def snapshot_player_state(player: Any) -> Dict[str, Any]:
    """Return a compact structured snapshot for action deltas."""
    ensure_playtest_state(player)
    state: Dict[str, Any] = {
        "month": _safe_int(getattr(player, "month", 1), 1),
        "action_in_month": _safe_int(getattr(player, "action_in_month", 1), 1),
        "total_actions": _safe_int(getattr(player, "total_actions", 0)),
        "realm": player.realm_name() if hasattr(player, "realm_name") else "",
    }
    for field in SNAPSHOT_FIELDS:
        state[field] = _safe_int(getattr(player, field, 0))

    state["materials"] = {
        "herbs": _safe_int(getattr(player, "herbs", 0)),
        "aged_herbs_10": _safe_int(getattr(player, "aged_herbs_10", 0)),
        "aged_herbs_30": _safe_int(getattr(player, "aged_herbs_30", 0)),
        "pills": _safe_int(getattr(player, "pills", 0)),
        "market_inventory": _clean_int_mapping(getattr(player, "market_inventory", {})),
    }
    state["alchemy_material_total"] = material_total(player)
    state["spirit_fields"] = _spirit_field_snapshot(player)
    state["equipment_count"] = equipment_count(player)
    state["equipment_score"] = equipment_score(player)
    state["equipped_items"] = _clean_str_mapping(getattr(player, "equipped_items", {}))
    state["equipment_inventory"] = _clean_int_mapping(getattr(player, "equipment_inventory", {}))
    state["equipment_history_count"] = len(_safe_list(getattr(player, "equipment_history", [])))
    state["furnace"] = str(current_furnace(player).get("name", "无专用丹炉"))
    state["action_counts"] = _clean_int_mapping(getattr(player, "monthly_action_counts", {}))
    state["event_log_count"] = len(_safe_list(getattr(player, "monthly_event_log", [])))
    state["risks"] = {field: _safe_int(getattr(player, field, 0)) for field in RISK_FIELDS}
    return state


def _spirit_field_snapshot(player: Any) -> Dict[str, int]:
    fields = _safe_list(getattr(player, "spirit_fields", []))
    planted = 0
    mature = 0
    withered = 0
    for field in fields:
        if not isinstance(field, dict):
            continue
        if field.get("withered"):
            withered += 1
            continue
        if field.get("crop_id"):
            planted += 1
            if _safe_int(field.get("months_left", 0)) <= 0:
                mature += 1
    return {
        "count": len(fields),
        "planted": planted,
        "mature": mature,
        "withered": withered,
    }


def compute_state_delta(before: Dict[str, Any] | None, after: Dict[str, Any] | None) -> Dict[str, int]:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {}
    delta: Dict[str, int] = {}
    numeric_fields = list(SNAPSHOT_FIELDS) + [
        "total_actions",
        "equipment_count",
        "equipment_score",
        "alchemy_material_total",
    ]
    for field in numeric_fields:
        diff = _safe_int(after.get(field, 0)) - _safe_int(before.get(field, 0))
        if diff:
            delta[field] = diff
    return delta


def record_action(
    player: Any,
    action_type: str,
    action_name: str,
    before: Dict[str, Any] | None,
    after: Dict[str, Any] | None,
    *,
    tags: Iterable[str] | None = None,
    notes: Iterable[str] | None = None,
    events: Iterable[str] | None = None,
) -> None:
    """Append one action log entry. Failures are swallowed by callers."""
    ensure_playtest_state(player)
    before = before if isinstance(before, dict) else {}
    after = after if isinstance(after, dict) else {}
    normalized_type = normalize_action_type(action_type)
    delta = compute_state_delta(before, after)
    entry = {
        "month": _safe_int(before.get("month", after.get("month", 1)), 1),
        "action_index": _safe_int(before.get("action_in_month", after.get("action_in_month", 1)), 1),
        "total_actions_before": _safe_int(before.get("total_actions", 0)),
        "total_actions_after": _safe_int(after.get("total_actions", before.get("total_actions", 0))),
        "action_type": normalized_type,
        "action_name": str(action_name or action_type_label(normalized_type)),
        "before": before,
        "after": after,
        "delta": delta,
        "tags": list(tags or _default_action_tags(normalized_type, delta)),
        "notes": [str(note) for note in list(notes or []) if str(note)],
        "events_triggered": list(events or _event_changes(before, after)),
        "items_gained": _items_gained(delta),
        "equipment_changes": _equipment_changes(before, after, delta),
        "risk_changes": _risk_changes(delta),
    }
    player.action_log.append(entry)
    player.action_log = player.action_log[-ACTION_LOG_LIMIT:]


def _default_action_tags(action_type: str, delta: Dict[str, int]) -> List[str]:
    tags = [normalize_action_type(action_type)]
    if any(delta.get(field, 0) > 0 for field in ("cultivation_progress", "cultivation", "realm_level")):
        tags.append("cultivation")
    if any(delta.get(field, 0) > 0 for field in RESOURCE_FIELDS):
        tags.append("resource")
    if any(delta.get(field, 0) > 0 for field in RISK_FIELDS):
        tags.append("risk")
    if delta.get("equipment_score", 0) or delta.get("equipment_count", 0):
        tags.append("equipment")
    return tags


def _event_changes(before: Dict[str, Any], after: Dict[str, Any]) -> List[str]:
    event_delta = _safe_int(after.get("event_log_count", 0)) - _safe_int(before.get("event_log_count", 0))
    if event_delta <= 0:
        return []
    return [f"第一章事件+{event_delta}"]


def _items_gained(delta: Dict[str, int]) -> List[str]:
    gained: List[str] = []
    for field in RESOURCE_FIELDS:
        value = delta.get(field, 0)
        if value > 0:
            gained.append(f"{FIELD_LABELS.get(field, field)}+{value}")
    if delta.get("alchemy_material_total", 0) > 0:
        gained.append(f"炼丹材料+{delta['alchemy_material_total']}")
    return gained


def _equipment_changes(before: Dict[str, Any], after: Dict[str, Any], delta: Dict[str, int]) -> List[str]:
    changes: List[str] = []
    history_delta = _safe_int(after.get("equipment_history_count", 0)) - _safe_int(before.get("equipment_history_count", 0))
    if history_delta > 0:
        changes.append(f"装备记录+{history_delta}")
    if before.get("equipped_items", {}) != after.get("equipped_items", {}):
        changes.append("当前装备变化")
    if delta.get("equipment_count", 0):
        changes.append(f"装备数量{delta['equipment_count']:+d}")
    if delta.get("equipment_score", 0):
        changes.append(f"装备评分{delta['equipment_score']:+d}")
    return changes


def _risk_changes(delta: Dict[str, int]) -> List[str]:
    changes: List[str] = []
    for field in RISK_FIELDS:
        value = delta.get(field, 0)
        if value:
            changes.append(f"{FIELD_LABELS.get(field, field)}{value:+d}")
    return changes


def summarize_month(
    player: Any,
    month: int,
    *,
    before_event: Dict[str, Any] | None = None,
    after_event: Dict[str, Any] | None = None,
    events: Iterable[str] | None = None,
    notes: Iterable[str] | None = None,
) -> Dict[str, Any]:
    ensure_playtest_state(player)
    target_month = max(1, _safe_int(month, 1))
    entries = [
        entry
        for entry in player.action_log
        if _safe_int(entry.get("month", 0)) == target_month
    ]
    action_counts = Counter(normalize_action_type(str(entry.get("action_type", "unknown"))) for entry in entries)
    action_delta = _sum_entry_deltas(entries)
    month_end_delta = compute_state_delta(before_event, after_event)
    total_delta = defaultdict(int)
    for source in (action_delta, month_end_delta):
        for field, value in source.items():
            total_delta[field] += value

    event_list = [str(event) for event in list(events or []) if str(event)]
    note_list = [str(note) for note in list(notes or []) if str(note)]
    summary = {
        "month": target_month,
        "action_counts": dict(action_counts),
        "action_delta": dict(action_delta),
        "month_end_delta": dict(month_end_delta),
        "total_delta": dict(total_delta),
        "events": event_list,
        "notes": note_list,
        "profile": _month_profile(action_counts),
    }
    summary["text"] = format_monthly_summary(summary)
    player.monthly_summary_log = [
        entry
        for entry in player.monthly_summary_log
        if _safe_int(entry.get("month", 0)) != target_month
    ]
    player.monthly_summary_log.append(summary)
    player.monthly_summary_log = player.monthly_summary_log[-MONTHLY_SUMMARY_LIMIT:]
    return summary


def _sum_entry_deltas(entries: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    total: Dict[str, int] = defaultdict(int)
    for entry in entries:
        delta = entry.get("delta", {})
        if not isinstance(delta, dict):
            continue
        for field, value in delta.items():
            amount = _safe_int(value)
            if amount:
                total[str(field)] += amount
    return dict(total)


def format_monthly_summary(summary: Dict[str, Any]) -> str:
    month = _safe_int(summary.get("month", 1), 1)
    action_counts = summary.get("action_counts", {})
    total_delta = summary.get("total_delta", {})
    events = list(summary.get("events", []) or [])
    profile = str(summary.get("profile", "本月行动较分散。"))
    lines = [f"第 {month} 月总结："]
    lines.append(f"- 本月行动：{_format_action_counts(action_counts)}。")
    lines.append(f"- 主要收益：{_format_delta_list(total_delta, positive=True)}。")
    lines.append(f"- 主要损失：{_format_delta_list(total_delta, positive=False)}。")
    lines.append(f"- 风险变化：{_format_risk_delta(total_delta)}。")
    lines.append(f"- 事件：{ '；'.join(events) if events else '无额外事件记录' }。")
    lines.append(f"- 系统判断：{profile}")
    return "\n".join(lines)


def _format_action_counts(action_counts: Any) -> str:
    if not isinstance(action_counts, dict) or not action_counts:
        return "无记录"
    parts = []
    for action_type, count in sorted(action_counts.items(), key=lambda item: (-_safe_int(item[1]), str(item[0]))):
        if _safe_int(count) > 0:
            parts.append(f"{action_type_label(str(action_type))}{_safe_int(count)}次")
    return "，".join(parts) if parts else "无记录"


def _format_delta_list(delta: Any, *, positive: bool) -> str:
    if not isinstance(delta, dict):
        return "无明显变化"
    fields = [
        "realm_level",
        "cultivation_progress",
        "cultivation",
        "spirit_stones",
        "herbs",
        "aged_herbs_10",
        "aged_herbs_30",
        "pills",
        "contribution",
        "intelligence",
        "combat_exp",
        "attack",
        "defense",
        "speed",
        "foundation",
        "alchemy_material_total",
        "equipment_score",
    ]
    rows = []
    for field in fields:
        value = _safe_int(delta.get(field, 0))
        if positive and value > 0:
            rows.append(f"{FIELD_LABELS.get(field, field)}+{value}")
        if not positive and value < 0:
            rows.append(f"{FIELD_LABELS.get(field, field)}{value}")
    return "，".join(rows[:6]) if rows else "无明显变化"


def _format_risk_delta(delta: Any) -> str:
    if not isinstance(delta, dict):
        return "无明显变化"
    rows = []
    for field in RISK_FIELDS:
        value = _safe_int(delta.get(field, 0))
        if value:
            rows.append(f"{FIELD_LABELS.get(field, field)}{value:+d}")
    return "，".join(rows[:7]) if rows else "无明显变化"


def _month_profile(action_counts: Counter[str]) -> str:
    if not action_counts:
        return "本月缺少有效行动记录。"
    high_risk = sum(action_counts.get(key, 0) for key in ("blackwater", "theft", "demonic"))
    safe_types = {
        key
        for key in ("meditation", "herb_gathering", "alchemy", "market", "farm", "social", "spell_training")
        if action_counts.get(key, 0) > 0
    }
    if action_counts.get("meditation", 0) >= 2 and len(safe_types) <= 1:
        return "本月偏闭关。"
    if high_risk >= 2:
        return "本月明显接触高风险路线。"
    if high_risk == 1:
        return "本月有一次高风险尝试，需要继续观察后续代价。"
    if {"herb_gathering", "alchemy"}.issubset(safe_types) or {"farm", "alchemy"}.issubset(safe_types):
        return "本月偏资源与炼丹准备。"
    if len(safe_types) >= 3:
        return "本月偏随心混合。"
    if action_counts.get("market", 0) or action_counts.get("equipment", 0):
        return "本月偏坊市与装备准备。"
    return "本月行动较稳。"


def summarize_run(player: Any, tournament_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ensure_playtest_state(player)
    entries = [entry for entry in player.action_log if isinstance(entry, dict)]
    action_counts = Counter(normalize_action_type(str(entry.get("action_type", "unknown"))) for entry in entries)
    benefit_sources = _benefit_sources(entries)
    risk_sources = _risk_sources(entries)
    summary = {
        "action_counts": dict(action_counts),
        "stage_profiles": _stage_profiles(entries),
        "benefit_sources": benefit_sources,
        "risk_sources": risk_sources,
        "npc_reactions": _npc_reaction_summary(player),
        "tournament_analysis": _tournament_analysis(player, tournament_result),
        "next_run_suggestions": _next_run_suggestions(player, tournament_result, action_counts),
    }
    return summary


def format_playtest_report(player: Any, tournament_result: Dict[str, Any] | None = None) -> str:
    summary = summarize_run(player, tournament_result)
    lines = ["\n===== 试玩行为分析 ====="]
    lines.append("本局行动统计：")
    action_counts = summary["action_counts"]
    if isinstance(action_counts, dict) and action_counts:
        for action_type, count in sorted(action_counts.items(), key=lambda item: (-_safe_int(item[1]), str(item[0]))):
            if _safe_int(count) > 0:
                lines.append(f"- {action_type_label(str(action_type))}：{_safe_int(count)}次")
    else:
        lines.append("- 暂无行动记录")

    lines.append("阶段倾向：")
    for profile in list(summary.get("stage_profiles", [])):
        lines.append(f"- {profile}")

    lines.append("主要收益来源：")
    for row in list(summary.get("benefit_sources", [])) or ["暂无明显收益来源记录。"]:
        lines.append(f"- {row}")

    lines.append("主要风险来源：")
    for row in list(summary.get("risk_sources", [])) or ["暂无明显风险来源记录。"]:
        lines.append(f"- {row}")

    lines.append("本局 NPC 反应：")
    for row in list(summary.get("npc_reactions", [])) or ["暂无明显 NPC 反应记录。"]:
        lines.append(f"- {row}")

    lines.append("大比表现分析：")
    for row in list(summary.get("tournament_analysis", [])):
        lines.append(f"- {row}")

    lines.append("下一局建议：")
    for row in list(summary.get("next_run_suggestions", [])):
        lines.append(f"- {row}")
    return "\n".join(lines)


def _npc_reaction_summary(player: Any) -> List[str]:
    rows: List[str] = []
    seen: set[str] = set()
    for entry in list(getattr(player, "npc_reaction_log", []) or [])[-8:]:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title", ""))
        npcs = [str(npc) for npc in list(entry.get("npc_ids", []) or []) if str(npc)]
        npc_text = "、".join(npcs) if npcs else "旁人"
        if not title:
            continue
        line = f"{npc_text}：{title}"
        if line in seen:
            continue
        seen.add(line)
        rows.append(line)
    flags = [str(flag) for flag in list(getattr(player, "npc_flags", []) or [])[-5:] if str(flag)]
    if flags:
        rows.append("留下的反应标记：" + "、".join(flags))
    impressions = {
        str(npc): _safe_int(value)
        for npc, value in dict(getattr(player, "npc_impressions", {}) or {}).items()
        if _safe_int(value)
    }
    if impressions:
        impression_text = "、".join(
            f"{npc}{value:+d}"
            for npc, value in sorted(impressions.items(), key=lambda item: (-abs(item[1]), item[0]))[:5]
        )
        rows.append("NPC 印象变化：" + impression_text)
    return rows[:8]


def _stage_profiles(entries: List[Dict[str, Any]]) -> List[str]:
    stages = [("前期", 1, 4), ("中期", 5, 8), ("后期", 9, 12)]
    rows: List[str] = []
    for label, start, end in stages:
        stage_entries = [
            entry
            for entry in entries
            if start <= _safe_int(entry.get("month", 0)) <= end
        ]
        if not stage_entries:
            rows.append(f"{label}暂无有效记录。")
            continue
        counts = Counter(normalize_action_type(str(entry.get("action_type", "unknown"))) for entry in stage_entries)
        top = [
            action_type_label(action_type)
            for action_type, count in counts.most_common(2)
            if count > 0
        ]
        rows.append(f"{label}偏向{'和'.join(top) if top else '分散行动'}。")
    return rows


def _benefit_sources(entries: List[Dict[str, Any]]) -> List[str]:
    cultivation_by_action: Dict[str, int] = defaultdict(int)
    resource_by_action: Dict[str, int] = defaultdict(int)
    combat_by_action: Dict[str, int] = defaultdict(int)
    equipment_by_action: Dict[str, int] = defaultdict(int)
    for entry in entries:
        action_type = normalize_action_type(str(entry.get("action_type", "unknown")))
        delta = entry.get("delta", {})
        if not isinstance(delta, dict):
            continue
        cultivation_by_action[action_type] += max(0, _safe_int(delta.get("cultivation_progress", 0)))
        cultivation_by_action[action_type] += max(0, _safe_int(delta.get("cultivation", 0))) * 2
        resource_by_action[action_type] += max(0, _safe_int(delta.get("spirit_stones", 0)))
        resource_by_action[action_type] += max(0, _safe_int(delta.get("herbs", 0)))
        resource_by_action[action_type] += max(0, _safe_int(delta.get("aged_herbs_10", 0))) * 3
        resource_by_action[action_type] += max(0, _safe_int(delta.get("aged_herbs_30", 0))) * 8
        resource_by_action[action_type] += max(0, _safe_int(delta.get("pills", 0))) * 4
        resource_by_action[action_type] += max(0, _safe_int(delta.get("alchemy_material_total", 0)))
        combat_by_action[action_type] += max(0, _safe_int(delta.get("combat_exp", 0)))
        combat_by_action[action_type] += max(0, _safe_int(delta.get("attack", 0)))
        combat_by_action[action_type] += max(0, _safe_int(delta.get("defense", 0)))
        combat_by_action[action_type] += max(0, _safe_int(delta.get("speed", 0)))
        equipment_by_action[action_type] += max(0, _safe_int(delta.get("equipment_score", 0)))

    rows: List[str] = []
    cultivation_source = _top_source(cultivation_by_action)
    if cultivation_source:
        rows.append(f"修为主要来自{cultivation_source}。")
    resource_source = _top_source(resource_by_action)
    if resource_source:
        rows.append(f"资源主要来自{resource_source}。")
    combat_source = _top_source(combat_by_action)
    if combat_source:
        rows.append(f"实战准备主要来自{combat_source}。")
    equipment_source = _top_source(equipment_by_action)
    if equipment_source:
        rows.append(f"装备提升主要来自{equipment_source}。")
    return rows[:5]


def _risk_sources(entries: List[Dict[str, Any]]) -> List[str]:
    risk_by_action: Dict[str, int] = defaultdict(int)
    risk_details: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for entry in entries:
        action_type = normalize_action_type(str(entry.get("action_type", "unknown")))
        delta = entry.get("delta", {})
        if not isinstance(delta, dict):
            continue
        for field in RISK_FIELDS:
            value = max(0, _safe_int(delta.get(field, 0)))
            if value:
                risk_by_action[action_type] += value
                risk_details[action_type][field] += value
    rows: List[str] = []
    for action_type, score in sorted(risk_by_action.items(), key=lambda item: -item[1])[:3]:
        details = "、".join(
            f"{FIELD_LABELS.get(field, field)}+{value}"
            for field, value in sorted(risk_details[action_type].items(), key=lambda item: -item[1])[:3]
        )
        rows.append(f"{action_type_label(action_type)}带来{details}。")
    return rows


def _top_source(scores: Dict[str, int]) -> str:
    positive = [(action_type, score) for action_type, score in scores.items() if score > 0]
    if not positive:
        return ""
    positive.sort(key=lambda item: (-item[1], item[0]))
    return action_type_label(positive[0][0])


def _tournament_analysis(player: Any, result: Dict[str, Any] | None) -> List[str]:
    rows: List[str] = []
    if result:
        rows.append(f"大比总分{_safe_int(result.get('total', 0))}/100，名次第{_safe_int(result.get('rank', 0))}名。")
        scores = result.get("scores", {})
        if isinstance(scores, dict):
            rows.append(
                "分项表现："
                f"问心{_safe_int(scores.get('测灵问心', 0))}/25，"
                f"试炼{_safe_int(scores.get('百药山试炼', 0))}/35，"
                f"斗法{_safe_int(scores.get('斗法台', 0))}/40。"
            )
        if _safe_int(result.get("practice_pressure_adjustment", 0)) < 0:
            rows.append("闭关疲劳或资源缺口已经进入大比扣分项。")
        if _safe_int(result.get("theft_tournament_adjustment", 0)) < 0:
            rows.append("盗术痕迹对大比评价形成负面修正。")
        if _safe_int(result.get("heishui_intel_bonus", 0)) > 0:
            rows.append("黑水或情报准备对分项有正向帮助。")
        if _safe_int(result.get("equipment_score", 0)) > 0:
            rows.append(f"装备评分为{_safe_int(result.get('equipment_score', 0))}，已参与临场准备。")
    if _safe_int(getattr(player, "realm_level", 1)) >= 4 or _safe_int(getattr(player, "cultivation_progress", 0)) >= 65:
        rows.append("修为基础较强。")
    else:
        rows.append("修为基础仍有提升空间。")
    if _safe_int(getattr(player, "combat_exp", 0)) >= 12 or _safe_int(getattr(player, "attack", 0)) >= 18:
        rows.append("实战准备不算薄弱。")
    else:
        rows.append("实战准备偏低。")
    if _safe_int(getattr(player, "intelligence", 0)) >= 12:
        rows.append("情报准备较充分。")
    elif _safe_int(getattr(player, "intelligence", 0)) <= 4:
        rows.append("情报准备偏少。")
    if _safe_int(getattr(player, "meditation_fatigue", 0)) > 0:
        rows.append(f"冥坐疲劳累计到{_safe_int(getattr(player, 'meditation_fatigue', 0))}。")
    return rows[:8]


def _next_run_suggestions(player: Any, result: Dict[str, Any] | None, action_counts: Counter[str]) -> List[str]:
    rows: List[str] = []
    rank = _safe_int(result.get("rank", 99), 99) if isinstance(result, dict) else 99
    if rank > 10:
        if _safe_int(getattr(player, "combat_exp", 0)) < 12:
            rows.append("若想冲击前十，可以在大比前补一次法术训练、装备准备或情报打听。")
        elif _safe_int(getattr(player, "cultivation_progress", 0)) < 60:
            rows.append("若想冲击前十，可以保持主路线同时补一点稳定修炼。")
        else:
            rows.append("若想冲击前十，可以观察资源、情报和装备三项中哪一项最短。")
    else:
        rows.append("当前节奏已能进入前十，可以继续观察不同随机事件下的稳定性。")

    high_risk_count = sum(action_counts.get(key, 0) for key in ("blackwater", "theft", "demonic"))
    if high_risk_count and (
        _safe_int(getattr(player, "exposure", 0)) >= 50
        or _safe_int(getattr(player, "karma", 0)) >= 25
        or _safe_int(getattr(player, "tracking_marks", 0)) > 0
    ):
        rows.append("高风险路线已有后患，下一局可保留爆点但留出一次收尾或降风险行动。")
    if _safe_int(getattr(player, "cultivation_pressure", 0)) > 0:
        rows.append("多线铺开时可以提前留灵石、丹药或灵草，避免后期修行缺口。")
    return rows[:3]
