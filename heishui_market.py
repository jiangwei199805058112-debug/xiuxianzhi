"""配置驱动的黑水坊市系统。"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import random
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from player import Player

CONFIG_DIR = Path(__file__).resolve().parent / "configs" / "heishui_market"


@dataclass(frozen=True)
class MarketConfig:
    items: List[Dict[str, Any]]
    shops: List[Dict[str, Any]]
    npcs: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    refresh_rules: List[Dict[str, Any]]
    unlock_rules: List[Dict[str, Any]]
    enums: List[Dict[str, Any]]
    blindbox_pools: List[Dict[str, Any]]
    risk_events: List[Dict[str, Any]]


_CONFIG_CACHE: Optional[MarketConfig] = None


def _load_json(filename: str) -> List[Dict[str, Any]]:
    path = CONFIG_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"黑水坊市配置缺失：{path}。请确认 configs/heishui_market 已随仓库提交。"
        )
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{filename} 的根节点必须是数组。")
    return [row for row in data if isinstance(row, dict)]


def _read_choice(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def load_config() -> MarketConfig:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = MarketConfig(
            items=_load_json("items.json"),
            shops=_load_json("shops.json"),
            npcs=_load_json("npcs.json"),
            events=_load_json("market_events.json"),
            refresh_rules=_load_json("refresh_rules.json"),
            unlock_rules=_load_json("unlock_rules.json"),
            enums=_load_json("enums.json"),
            blindbox_pools=_load_json("blindbox_pools.json"),
            risk_events=_load_json("heishui_risk_events.json"),
        )
    return _CONFIG_CACHE


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _first_number(text: Any, default: int = 0) -> int:
    match = re.search(r"-?\d+", str(text))
    return int(match.group(0)) if match else default


def _split_tags(value: Any) -> List[str]:
    text = str(value or "").replace("，", ",").replace("、", ",").replace("/", ",")
    return [part.strip() for part in text.split(",") if part.strip()]


def _parse_weight_table(value: Any) -> List[Tuple[str, int]]:
    rows: List[Tuple[str, int]] = []
    for part in _split_tags(value):
        if ":" not in part:
            continue
        name, weight_text = part.split(":", 1)
        rows.append((name.strip(), max(1, _to_int(weight_text, 1))))
    return rows


def _weighted_choice(weighted_rows: List[Tuple[Any, int]]) -> Any:
    if not weighted_rows:
        return None
    total = sum(max(1, weight) for _, weight in weighted_rows)
    roll = random.uniform(0, total)
    cursor = 0.0
    for value, weight in weighted_rows:
        cursor += max(1, weight)
        if roll <= cursor:
            return value
    return weighted_rows[-1][0]


def _effect_label(attr: str) -> str:
    labels = {
        "spirit_stones": "灵石",
        "herbs": "普通灵草",
        "pills": "丹药",
        "talisman_fire": "火弹符",
        "black_market_clue": "黑市线索",
        "exposure": "暴露度",
        "heart_demon": "心魔值",
        "demonic_qi": "魔气值",
        "karma": "业力值",
        "tracking_marks": "追踪标记",
        "righteous_reputation": "正道声望",
        "hp": "气血",
        "attack": "攻击",
        "combat_exp": "斗法经验",
        "divine_sense": "神识",
    }
    return labels.get(attr, attr)


def _apply_effects_dict(player: Player, effects: Dict[str, Any]) -> List[str]:
    notes: List[str] = []
    for attr, value in effects.items():
        amount = _to_int(value)
        if amount == 0:
            continue
        if attr == "hp":
            player.hp = min(player.max_hp, player.hp + amount)
        else:
            setattr(player, attr, getattr(player, attr, 0) + amount)
        notes.append(f"{_effect_label(attr)}{amount:+d}")
    return notes


def _item_text_fields(item: Dict[str, Any]) -> str:
    fields = [
        "name",
        "category",
        "subtype",
        "grade",
        "rarity",
        "effect_type",
        "risk_tags",
        "story_tags",
    ]
    return ",".join(str(item.get(field, "")) for field in fields)


def _event_matches_item(event: Dict[str, Any], item: Dict[str, Any]) -> bool:
    item_text = _item_text_fields(item)
    return any(token and token in item_text for token in _split_tags(event.get("affected_categories")))


def _event_price_modifier(config: MarketConfig, event_ids: Iterable[str], item: Dict[str, Any]) -> int:
    modifier = 0
    events_by_id = {event["event_id"]: event for event in config.events}
    for event_id in event_ids:
        event = events_by_id.get(str(event_id))
        if event and _event_matches_item(event, item):
            modifier += _to_int(event.get("price_modifier_pct"))
    return max(-50, min(modifier, 150))


def _event_stock_modifier(config: MarketConfig, event_ids: Iterable[str], item: Dict[str, Any]) -> int:
    modifier = 0
    events_by_id = {event["event_id"]: event for event in config.events}
    for event_id in event_ids:
        event = events_by_id.get(str(event_id))
        if event and _event_matches_item(event, item):
            modifier += _to_int(event.get("stock_modifier_pct"))
    return max(-80, min(modifier, 150))


def _realm_level_from_text(text: str) -> Optional[int]:
    match = re.search(r"炼气([一二三四五六七八九]|\d+)层", text)
    if not match:
        return None
    chinese_digits = "一二三四五六七八九"
    token = match.group(1)
    return int(token) if token.isdigit() else chinese_digits.index(token) + 1


def _relation_for_text(player: Player, text: str, shop: Optional[Dict[str, Any]] = None) -> int:
    if "天机阁" in text:
        return _npc_relation(player, "npc_bailao")
    if "风月楼" in text or "红袖" in text:
        return _npc_relation(player, "npc_tingqin")
    if "炎大师" in text:
        return _npc_relation(player, "npc_yandashi")
    if shop:
        return _npc_relation(player, shop.get("npc_id"))
    return 0


def _condition_token_ok(player: Player, token: str, shop: Optional[Dict[str, Any]] = None) -> bool:
    token = token.strip()
    if not token:
        return True
    if "并" in token:
        return all(_condition_token_ok(player, part, shop) for part in token.split("并"))
    if any(keyword in token for keyword in ("凡人", "可进", "随机", "支付入市费")):
        return True
    if "持有本月暗号" in token:
        return player.has_black_market_password and player.black_market_password_month == player.month
    if "购买 svc_tianji_heishi" in token:
        return player.has_black_market_password or player.black_market_clue > 0
    if "炼丹副职" in token or "宗门招徒事件开启" in token:
        return False

    realm_level = _realm_level_from_text(token)
    if realm_level is not None:
        return player.realm_level >= realm_level

    checks = [
        (r"神识\s*[≥>=]\s*(\d+)", player.divine_sense),
        (r"业力\s*[≥>=]\s*(\d+)", player.karma),
        (r"魔气\s*[≥>=]\s*(\d+)", player.demonic_qi),
        (r"声望\s*[≥>=]\s*(\d+)", player.righteous_reputation),
        (r"累计消费\s*[≥>=]\s*(\d+)", player.heishui_market_spent),
    ]
    for pattern, value in checks:
        match = re.search(pattern, token)
        if match:
            return value >= int(match.group(1))

    relation_match = re.search(r"好感\s*[≥>=]\s*(\d+)", token)
    if relation_match:
        return _relation_for_text(player, token, shop) >= int(relation_match.group(1))

    return True


def _condition_ok(player: Player, text: Any, shop: Optional[Dict[str, Any]] = None) -> bool:
    condition = str(text or "").strip()
    if not condition:
        return True
    return any(_condition_token_ok(player, token, shop) for token in re.split(r"\s*(?:/|或)\s*", condition))


def _player_stage_ok(player: Player, text: Any) -> bool:
    return _condition_ok(player, text)


def _ensure_market_profiles(player: Player, config: Optional[MarketConfig] = None) -> None:
    config = config or load_config()
    for npc in config.npcs:
        npc_id = str(npc.get("npc_id"))
        if npc_id and npc_id not in player.heishui_npc_affection:
            player.heishui_npc_affection[npc_id] = _to_int(npc.get("initial_relation"))
    player.clamp()


def _npc_relation(player: Player, npc_id: Any) -> int:
    if not npc_id:
        return 0
    return _to_int(player.heishui_npc_affection.get(str(npc_id), 0))


def shop_unlock_reason(player: Player, shop: Dict[str, Any]) -> Tuple[bool, str]:
    shop_id = str(shop.get("shop_id", ""))
    if shop_id == "shop_heishi":
        if player.has_black_market_password and player.black_market_password_month == player.month:
            return True, "持有本月暗号"
        if player.karma >= 10 or player.demonic_qi >= 10 or player.black_market_clue > 0:
            return True, "黑市中人主动接触"
        return False, "需要天机阁暗号、业力、魔气或黑市线索"

    if shop_id == "shop_zhenbao":
        if player.heishui_market_spent >= 1000 or player.righteous_reputation >= 100:
            return True, "贵宾资格满足"
        return False, "累计消费或声望不足"

    if _to_int(shop.get("base_reputation_req")) > player.righteous_reputation:
        return False, "正道声望不足"

    if shop_id in {"shop_baibing", "shop_yushou"} and player.realm_level < 3:
        return False, "境界不足"

    if not _condition_ok(player, shop.get("unlock_condition"), shop):
        return False, "条件不足"

    return True, "可进入"


def available_shops(player: Player) -> List[Dict[str, Any]]:
    config = load_config()
    _ensure_market_profiles(player, config)
    shops: List[Dict[str, Any]] = []
    for shop in config.shops:
        unlocked, reason = shop_unlock_reason(player, shop)
        if unlocked:
            item = dict(shop)
            item["unlock_reason"] = reason
            shops.append(item)
    return shops


def _rule_for_shop(config: MarketConfig, shop_id: str) -> Dict[str, Any]:
    for rule in config.refresh_rules:
        if rule.get("shop_id") == shop_id:
            return rule
    return {}


def _eligible_items(config: MarketConfig, shop_id: str, rule: Dict[str, Any], player: Player) -> List[Dict[str, Any]]:
    categories = set(_split_tags(rule.get("eligible_categories")))
    shop = _find_shop(config, shop_id)
    if shop and shop_id != "shop_heishi" and not _condition_ok(player, rule.get("min_player_stage"), shop):
        return []
    eligible: List[Dict[str, Any]] = []
    for item in config.items:
        if item.get("shop_id") != shop_id:
            continue
        if categories and item.get("category") not in categories:
            continue
        if _to_int(item.get("stock_max")) <= 0:
            continue
        if not _condition_ok(player, item.get("unlock_condition"), shop):
            continue
        eligible.append(item)
    return eligible


def _modified_weight(config: MarketConfig, item: Dict[str, Any], shop: Dict[str, Any], player: Player) -> int:
    base = max(1, _to_int(item.get("refresh_weight"), 1))
    shop_id = str(shop.get("shop_id"))
    if shop_id == "shop_tanwei":
        base += player.luck * 2
    if shop_id == "shop_fengyue":
        base += player.charm * 2 + _npc_relation(player, shop.get("npc_id")) // 5
    if shop_id == "shop_tianji":
        base += _npc_relation(player, shop.get("npc_id")) // 5
    if shop_id == "shop_heishi":
        base += int(player.karma * 1.5 + player.demonic_qi * 2)
    base += _event_stock_modifier(config, player.heishui_market_events, item)
    return max(1, base)


def _weighted_sample(items: List[Dict[str, Any]], weights: List[int], count: int) -> List[Dict[str, Any]]:
    pool = list(zip(items, weights))
    selected: List[Dict[str, Any]] = []
    for _ in range(min(count, len(pool))):
        total = sum(weight for _, weight in pool)
        roll = random.uniform(0, total)
        cursor = 0.0
        chosen_index = 0
        for index, (_, weight) in enumerate(pool):
            cursor += weight
            if roll <= cursor:
                chosen_index = index
                break
        selected.append(pool.pop(chosen_index)[0])
    return selected


def _make_stock_entry(config: MarketConfig, item: Dict[str, Any], shop: Dict[str, Any], player: Player) -> Dict[str, Any]:
    price_low = _to_int(item.get("price_min"), 1)
    price_high = max(price_low, _to_int(item.get("price_max"), price_low))
    base_price = random.randint(price_low, price_high)
    price_modifier_pct = _event_price_modifier(config, player.heishui_market_events, item)
    if player.heishui_price_modifier_month == player.month:
        item_text = _item_text_fields(item)
        for category, modifier in player.heishui_price_modifiers.items():
            if category and category in item_text:
                price_modifier_pct += _to_int(modifier)
    price_modifier_pct = max(-50, min(price_modifier_pct, 150))
    event_price_modifier = 1 + price_modifier_pct / 100
    shop_multiplier = float(shop.get("price_multiplier") or 1.0)
    price = max(1, int(round(base_price * shop_multiplier * event_price_modifier)))

    stock_low = _to_int(item.get("stock_min"), 0)
    stock_high = max(stock_low, _to_int(item.get("stock_max"), stock_low))
    base_stock = random.randint(stock_low, stock_high)
    stock_modifier = 1 + _event_stock_modifier(config, player.heishui_market_events, item) / 100
    stock = max(1, int(round(base_stock * stock_modifier)))
    return {"item_id": item["item_id"], "price": price, "stock": stock}


def _refresh_shop_stock(config: MarketConfig, shop: Dict[str, Any], player: Player) -> List[Dict[str, Any]]:
    shop_id = str(shop.get("shop_id"))
    rule = _rule_for_shop(config, shop_id)
    eligible = _eligible_items(config, shop_id, rule, player)
    if not eligible:
        return []

    fixed_count = _to_int(rule.get("fixed_stock_count"), _to_int(shop.get("fixed_stock_count")))
    random_count = _to_int(rule.get("random_stock_count"), _to_int(shop.get("random_stock_count")))
    weighted = sorted(
        eligible,
        key=lambda item: (_modified_weight(config, item, shop, player), _to_int(item.get("price_max"))),
        reverse=True,
    )
    fixed = weighted[: max(0, fixed_count)]
    remaining = [item for item in eligible if item not in fixed]

    if shop_id == "shop_tanwei" and random_count > 0:
        blindboxes = [
            item
            for item in remaining
            if item.get("category") == "盲盒" and item.get("can_trigger_event")
        ]
        if blindboxes:
            featured = min(blindboxes, key=lambda item: _to_int(item.get("price_min"), 999999))
            fixed.append(featured)
            remaining = [item for item in remaining if item != featured]
            random_count = max(0, random_count - 1)

    weights = [_modified_weight(config, item, shop, player) for item in remaining]
    random_items = _weighted_sample(remaining, weights, random_count)
    selected = fixed + random_items
    if shop_id == "shop_tianji":
        introductions = [
            item
            for item in eligible
            if "解锁黑市" in str(item.get("effect_type")) or "黑市" in str(item.get("effect_value"))
        ]
        if introductions and introductions[0] not in selected:
            selected.append(introductions[0])

    seen: set[str] = set()
    entries: List[Dict[str, Any]] = []
    for item in selected:
        item_id = str(item.get("item_id"))
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        entries.append(_make_stock_entry(config, item, shop, player))
    return entries


def ensure_market_state(player: Player, force: bool = False) -> None:
    config = load_config()
    _ensure_market_profiles(player, config)
    if not force and player.heishui_market_month == player.month and player.heishui_market_stock:
        return

    player.heishui_market_month = player.month
    event = random.choice(config.events) if config.events else None
    player.heishui_market_events = [str(event["event_id"])] if event else []
    player.heishui_market_stock = {}
    for shop in config.shops:
        shop_id = str(shop.get("shop_id"))
        player.heishui_market_stock[shop_id] = _refresh_shop_stock(config, shop, player)
    player.clamp()


def get_active_event_names(player: Player) -> List[str]:
    config = load_config()
    events = {str(event.get("event_id")): event for event in config.events}
    return [str(events[event_id]["name"]) for event_id in player.heishui_market_events if event_id in events]


def _find_item(config: MarketConfig, item_id: str) -> Optional[Dict[str, Any]]:
    for item in config.items:
        if item.get("item_id") == item_id:
            return item
    return None


def _find_shop(config: MarketConfig, shop_id: str) -> Optional[Dict[str, Any]]:
    for shop in config.shops:
        if shop.get("shop_id") == shop_id:
            return shop
    return None


def _stock_for_shop(player: Player, shop_id: str) -> List[Dict[str, Any]]:
    ensure_market_state(player)
    return player.heishui_market_stock.setdefault(shop_id, [])


def _append_log(player: Player, text: str) -> None:
    player.intelligence_log.append(text)
    if len(player.intelligence_log) > 30:
        player.intelligence_log = player.intelligence_log[-30:]


def _add_inventory(player: Player, item: Dict[str, Any], count: int = 1) -> None:
    item_id = str(item.get("item_id"))
    if item_id:
        player.market_inventory[item_id] = player.market_inventory.get(item_id, 0) + count


def _apply_risk(player: Player, item: Dict[str, Any], shop: Dict[str, Any], price: int) -> List[str]:
    notes: List[str] = []
    risk_tags = set(_split_tags(item.get("risk_tags")))
    side_effect = str(item.get("side_effect", ""))
    if price >= 80 or "高价暴露" in risk_tags:
        gain = max(1, price // 100)
        player.exposure += gain
        notes.append(f"高价交易，暴露度+{gain}")
    if "暴露" in risk_tags:
        player.exposure += 2
        notes.append("暴露度+2")
    if "黑市接触" in risk_tags or "黑市" in risk_tags:
        player.exposure += 3
        notes.append("黑市接触，暴露度+3")
    if shop.get("is_black_market"):
        player.karma += 2
        player.demonic_qi += 2
        player.exposure += 3
        notes.append("黑市交易，业力+2，魔气+2，暴露度+3")
    if "魔气" in risk_tags:
        player.demonic_qi += 2
        notes.append("魔气+2")
    if "业力" in risk_tags or "黑货" in risk_tags:
        player.karma += 2
        notes.append("业力+2")
    if "心魔" in risk_tags:
        player.heart_demon += 3
        notes.append("心魔值+3")
    if "寿元损失" in risk_tags:
        player.max_hp -= 2
        player.hp = min(player.hp, player.max_hp)
        notes.append("根基受损，气血上限-2")
    if "盘查" in risk_tags or "追踪" in risk_tags:
        player.exposure += 3
        player.tracking_marks += 1
        notes.append("被盯梢风险上升")
    if {"被监听", "被察觉", "身份曝光", "仇恨", "黑袍道人"} & risk_tags:
        player.exposure += 4
        player.tracking_marks += 1
        notes.append("身份风险上升")
    if "丹毒" in risk_tags:
        player.heart_demon += 1
        notes.append("丹毒扰心，心魔值+1")
    exposure_match = re.search(r"暴露度\s*\+\s*(\d+)", side_effect)
    if exposure_match:
        gain = int(exposure_match.group(1))
        player.exposure += gain
        notes.append(f"副作用：暴露度+{gain}")
    return notes


def _apply_numeric_effect(player: Player, attr: str, amount: int) -> None:
    if attr == "hp":
        player.hp = min(player.max_hp, player.hp + amount)
    else:
        setattr(player, attr, getattr(player, attr) + amount)


def _roll_intel_quality(item: Dict[str, Any]) -> str:
    pool = _parse_weight_table(item.get("quality_pool"))
    if not pool:
        return str(item.get("grade") or "普通情报")
    return str(_weighted_choice(pool))


def _quality_power(quality: str) -> int:
    if quality == "精准情报":
        return 2
    if quality in {"普通情报", "公开消息", "隐秘消息", "精良"}:
        return 1
    if quality == "稀有":
        return 2
    if quality == "模糊情报":
        return 1 if random.random() < 0.55 else 0
    if quality == "错误情报":
        return -1
    return 0


def _add_tournament_intel_bonus(player: Player, section: str, amount: int) -> None:
    current = _to_int(player.heishui_tournament_bonuses.get(section))
    player.heishui_tournament_bonuses[section] = max(-2, min(2, current + amount))


def _apply_intel_service(player: Player, item: Dict[str, Any], notes: List[str]) -> List[str]:
    name = str(item.get("name", "情报"))
    effect_type = str(item.get("effect_type", ""))
    effect_value = str(item.get("effect_value", ""))
    quality = _roll_intel_quality(item)
    power = _quality_power(quality)
    player.heishui_intel_purchase_count += 1
    player.intelligence += 1 if power >= 0 else 0
    _append_log(player, f"{name}（{quality}）：{effect_value}")
    notes.append(f"情报品质：{quality}")

    if "解锁黑市" in effect_type:
        player.has_black_market_password = True
        player.black_market_password_month = player.month
        player.black_market_clue += 1
        player.heishui_black_intro_count += 1
        notes.append("获得本月黑市暗号，暗坊黑市已解锁")
        notes.append("情报写入日志")
        return notes

    if quality == "过期情报":
        notes.append("情报已经过期，没有实际效果")
        notes.append("情报写入日志")
        return notes

    if "百药山灵草线索" in effect_type or "探索" in str(item.get("subtype", "")):
        if power > 0:
            player.explore_intel_bonus += power
            notes.append(f"下一次百药山采药情报修正+{power}")
        elif power < 0:
            player.exposure += 3
            notes.append("误信采药传闻，暴露度+3")
    elif "大比对手情报" in effect_type or "家族情报" in str(item.get("subtype", "")):
        section = random.choice(["mind", "trial", "combat"])
        _add_tournament_intel_bonus(player, section, power)
        section_name = {"mind": "测灵问心", "trial": "百药山试炼", "combat": "斗法台"}[section]
        if power >= 0:
            notes.append(f"{section_name}获得小幅情报修正")
        else:
            player.heart_demon += 1
            notes.append(f"{section_name}情报误导，心魔值+1")
    elif "坊市行情消息" in effect_type or "价格预测" in effect_type:
        categories = _split_tags(item.get("market_categories")) or ["丹药", "符箓", "盲盒", "黑市道具"]
        category = random.choice(categories)
        modifier = _to_int(item.get("price_modifier_pct"), -10)
        if power < 0:
            modifier = abs(modifier)
            player.exposure += 2
            notes.append("行情传闻反向，暴露度+2")
        elif power == 0:
            notes.append("行情消息模糊，只能作参考")
            notes.append("情报写入日志")
            return notes
        player.heishui_price_modifiers[category] = modifier * max(1, abs(power))
        player.heishui_price_modifier_month = min(12, player.month + 1)
        notes.append(f"下月{category}价格修正{player.heishui_price_modifiers[category]:+d}%")
    elif "黑市暗号线索" in effect_type or "黑市" in effect_value:
        player.heishui_black_intro_count += 1
        if power > 0:
            player.black_market_clue += power
            if power >= 2:
                player.has_black_market_password = True
                player.black_market_password_month = player.month
            notes.append("获得黑市暗号线索，暗坊黑市更容易解锁")
        elif power < 0:
            player.exposure += 5
            player.tracking_marks += 1
            notes.append("黑市暗号有误，暴露度+5，追踪标记+1")
    else:
        if power > 0:
            player.intelligence += power
            notes.append(f"情报值额外+{power}")
        elif power < 0:
            player.heart_demon += 1
            notes.append("情报误导，心魔值+1")

    notes.append("情报写入日志")
    return notes


def _apply_fengyue_service(player: Player, item: Dict[str, Any], shop: Dict[str, Any], price: int, notes: List[str]) -> List[str]:
    effect_type = str(item.get("effect_type", ""))
    npc_id = str(shop.get("npc_id", ""))
    if "听曲静心" in effect_type:
        drop = random.randint(3, 5)
        player.heart_demon -= drop
        player.dao_heart += 1
        notes.append(f"场景淡出处理：听曲静心，心魔值-{drop}，道心+1")
        return notes
    if "风月传闻" in effect_type or "获得传闻" in effect_type:
        fake_item = dict(item)
        fake_item["effect_type"] = random.choice(["百药山灵草线索", "大比对手情报", "坊市行情消息"])
        notes = _apply_intel_service(player, fake_item, notes)
        if random.random() < 0.35:
            player.exposure += 2
            notes.append("人多口杂，暴露度+2")
        return notes
    if "结识风月楼管事" in effect_type:
        player.heishui_npc_affection[npc_id] = player.heishui_npc_affection.get(npc_id, 0) + 8
        player.charm += 1
        notes.append("场景淡出处理：结识管事，风月楼关系+8，魅力+1")
        return notes

    player.dao_heart += 2
    player.heart_demon -= 3
    player.charm += 1 if price >= 10 else 0
    player.heishui_npc_affection[npc_id] = player.heishui_npc_affection.get(npc_id, 0) + 3
    notes.append("场景淡出处理：心境舒缓，人脉略增")
    return notes


def _apply_item_effect(player: Player, item: Dict[str, Any], shop: Dict[str, Any], price: int) -> List[str]:
    effect_type = str(item.get("effect_type", ""))
    effect_value = str(item.get("effect_value", ""))
    category = str(item.get("category", ""))
    name = str(item.get("name", ""))
    notes = _apply_risk(player, item, shop, price)
    number = _first_number(effect_value, 0)

    if category == "盲盒":
        notes.extend(_resolve_blindbox(player, item, price))
        return notes

    if category == "符箓":
        _apply_talisman(player, name, str(item.get("subtype", "")))
        notes.append("符箓已入袋，斗法可用")
        return notes

    if category == "情报服务" or "情报" in effect_type:
        return _apply_intel_service(player, item, notes)

    if category == "社交服务":
        return _apply_fengyue_service(player, item, shop, price, notes)

    if "气血恢复" in effect_type:
        recovery = max(5, player.max_hp * number // 100 if "%" in effect_value else number)
        _apply_numeric_effect(player, "hp", recovery)
        notes.append(f"气血恢复{recovery}")
    elif "灵气增加" in effect_type or "修炼增益" in effect_type:
        gain = max(3, number // 5 if number >= 20 else number)
        player.gain_cultivation_progress(gain)
        notes.append(f"修炼进度+{gain}")
    elif "灵力恢复" in effect_type:
        player.mp += max(5, number)
        notes.append("灵力恢复")
    elif "暴露度降低" in effect_type:
        player.exposure -= max(3, number)
        notes.append("暴露度下降")
    elif "神识" in effect_type:
        player.divine_sense += max(1, number)
        player.heart_demon -= 2
        notes.append("神识受益")
    elif "攻击" in effect_type or "伤害" in effect_type or "战力爆发" in effect_type:
        player.attack += max(1, number // 5 if number else 2)
        notes.append("攻击能力提升")
    elif "防御" in effect_type or "护盾" in effect_type:
        player.defense += max(1, number // 5 if number else 2)
        notes.append("防御能力提升")
    elif "逃跑" in effect_type or "闪避" in effect_type:
        player.speed += 2
        notes.append("身法提升")
    elif "境界提升" in effect_type and player.realm_level < 9:
        player.realm_level += 1
        player.heart_demon += 8
        player.karma += 5
        notes.append("境界强行提升，但心魔与业力上升")
    elif "残缺魔修手札" in effect_type:
        player.combat_exp += 2
        player.divine_sense += 1
        notes.append("斗法经验+2，神识+1")
    elif "来历不明聚气丹" in effect_type:
        player.gain_cultivation_progress(18)
        notes.append("修炼进度+18")
    elif "破损阵盘" in effect_type:
        player.exposure -= 4
        player.market_flags.append("破损阵盘")
        notes.append("你临时布下遮掩阵纹，暴露度-4")
    elif "假身份木牌" in effect_type:
        player.exposure -= 4
        player.market_flags.append("假身份木牌")
        notes.append("你多了一层假身份遮掩，暴露度-4")
    elif "支线开启" in effect_type or "法器升级" in effect_type or "副本解锁" in effect_type:
        player.market_flags.append(str(item.get("item_id")))
        notes.append("相关线索已记录")
    else:
        _add_inventory(player, item)
        notes.append("物品已收入行囊")

    return notes


def _apply_talisman(player: Player, name: str, subtype: str) -> None:
    if "避火" in name:
        player.talisman_avoid_fire += 1
    elif "防御" in subtype or "护身" in name or "金钟" in name:
        player.talisman_guard += 1
    elif "破甲" in name or "破甲" in subtype:
        player.talisman_break_armor += 1
    elif "攻击" in subtype or "火" in name:
        player.talisman_fire += 1
    elif "破" in name:
        player.talisman_break_armor += 1
    else:
        player.market_inventory[name] = player.market_inventory.get(name, 0) + 1


def _resolve_blindbox(player: Player, item: Dict[str, Any], price: int) -> List[str]:
    config = load_config()
    item_id = str(item.get("item_id"))
    pool = [
        row
        for row in config.blindbox_pools
        if item_id in _split_tags(row.get("item_ids"))
    ]
    notes: List[str] = []
    if not pool:
        player.heishui_blindbox_net -= price
        player.exposure += 3
        player.market_flags.append("未知盲盒")
        return [f"{item.get('name')}内里杂乱难辨，你暂时只觉亏损，暴露度+3"]

    weighted: List[Tuple[Dict[str, Any], int]] = []
    appraisal = player.luck * 2 + player.divine_sense // 2
    for outcome in pool:
        weight = max(1, _to_int(outcome.get("weight"), 1))
        quality = str(outcome.get("quality", ""))
        if quality in {"small", "medium", "unlock"}:
            weight += appraisal
        elif quality == "dark":
            weight += player.luck
        elif quality in {"loss", "tracked"}:
            weight = max(1, weight - appraisal // 2)
        weighted.append((outcome, weight))

    outcome = _weighted_choice(weighted)
    gain = random.randint(_to_int(outcome.get("stone_min")), _to_int(outcome.get("stone_max")))
    if gain:
        player.spirit_stones += gain
    effects = outcome.get("effects", {})
    if isinstance(effects, dict):
        notes.extend(_apply_effects_dict(player, effects))
    player.heishui_blindbox_net += gain - price
    if outcome.get("outcome_id") == "empty":
        player.market_flags.append("盲盒亏损")
    if outcome.get("outcome_id") == "tracked":
        player.market_flags.append("追踪标记")
    if outcome.get("outcome_id") == "black_clue":
        player.market_flags.append("黑市线索")
    if outcome.get("outcome_id") == "demonic_item":
        player.market_flags.append("魔道盲盒物")

    result_text = str(outcome.get("result_text") or f"{item.get('name')}开出{outcome.get('name')}")
    notes.append(f"{result_text} 盲盒净收益{gain - price:+d}灵石")
    return notes


def buy_item(player: Player, shop_id: str, item_id: str, quantity: int = 1) -> str:
    config = load_config()
    ensure_market_state(player)
    shop = _find_shop(config, shop_id)
    item = _find_item(config, item_id)
    if shop is None or item is None:
        return "交易失败：店铺或商品不存在。"
    unlocked, reason = shop_unlock_reason(player, shop)
    if not unlocked:
        return f"交易失败：{shop['shop_name']}未解锁（{reason}）。"
    stock = _stock_for_shop(player, shop_id)
    entry = next((row for row in stock if row.get("item_id") == item_id), None)
    if entry is None:
        return "交易失败：本月库存中没有这件商品。"
    if _to_int(entry.get("stock")) < quantity:
        return "交易失败：库存不足。"
    total_price = _to_int(entry.get("price")) * quantity
    if player.spirit_stones < total_price:
        return "交易失败：灵石不足。"

    player.spirit_stones -= total_price
    player.heishui_market_spent += total_price
    player.heishui_purchase_count += quantity
    category = str(item.get("category", ""))
    if category == "盲盒":
        player.heishui_blindbox_purchase_count += quantity
        if item_id == "item_blind_bloodbag":
            player.heishui_bloodbag_bought += quantity
            player.heishui_bloodbag_bought_this_month += quantity
            player.market_flags.append("买过沾血储物袋")
    if shop_id == "shop_heishi":
        player.heishui_black_market_purchase_count += quantity
        player.heishui_black_market_bought_this_month += quantity
        player.market_flags.append(f"黑市购物:{item_id}")
    entry["stock"] = _to_int(entry.get("stock")) - quantity
    if entry["stock"] <= 0:
        stock.remove(entry)

    notes: List[str] = []
    for _ in range(quantity):
        notes.extend(_apply_item_effect(player, item, shop, _to_int(entry.get("price"))))
    player.clamp()
    note_text = "；".join(notes) if notes else "无额外影响"
    return f"你在{shop['shop_name']}买下{item['name']}，花费{total_price}下品灵石。{note_text}。"


def buy_item_by_name(player: Player, item_name: str) -> str:
    config = load_config()
    ensure_market_state(player)
    for shop in config.shops:
        shop_id = str(shop.get("shop_id"))
        for entry in _stock_for_shop(player, shop_id):
            item = _find_item(config, str(entry.get("item_id")))
            if item and item.get("name") == item_name:
                return buy_item(player, shop_id, str(item.get("item_id")))
    return f"本月坊市未刷出：{item_name}。"


def sell_basic_resource(player: Player) -> str:
    print("可出售资源：")
    print("1. 普通灵草：2下品灵石")
    print("2. 十年份灵草：10下品灵石")
    print("3. 三十年份灵草：35下品灵石")
    choice = _read_choice("请选择出售项：")
    if choice == "1" and player.herbs > 0:
        player.herbs -= 1
        player.spirit_stones += 2
        return "你出售普通灵草，灵石+2。"
    if choice == "2" and player.aged_herbs_10 > 0:
        player.aged_herbs_10 -= 1
        player.spirit_stones += 10
        return "你出售十年份灵草，灵石+10。"
    if choice == "3" and player.aged_herbs_30 > 0:
        player.aged_herbs_30 -= 1
        player.spirit_stones += 35
        return "你出售三十年份灵草，灵石+35。"
    return "你没有完成出售。"


def consign_basic_resource(player: Player) -> str:
    if player.herbs <= 0:
        return "你没有可寄卖的普通灵草。"
    player.herbs -= 1
    expected_price = 3 + player.charm // 3
    player.consignment_items.append({"name": "普通灵草", "expected_price": expected_price, "month": player.month})
    player.heishui_npc_affection["npc_shenwanjin"] = player.heishui_npc_affection.get("npc_shenwanjin", 0) + 1
    player.clamp()
    return f"你把1株普通灵草挂到聚宝斋寄卖，预期成交价{expected_price}下品灵石。"


def settle_consignments(player: Player) -> str:
    if not player.consignment_items:
        return "本月没有寄卖物。"
    sold = 0
    income = 0
    remaining: List[Dict[str, Any]] = []
    for item in player.consignment_items:
        chance = 45 + player.charm * 3 + player.luck * 2
        if random.randint(1, 100) <= chance:
            sold += 1
            income += _to_int(item.get("expected_price"), 1)
        else:
            remaining.append(item)
    player.consignment_items = remaining
    player.spirit_stones += income
    player.clamp()
    return f"寄卖结算：成交{sold}件，灵石+{income}。"


def run_simple_auction(player: Player) -> str:
    config = load_config()
    auction_items = [item for item in config.items if item.get("category") == "拍卖品"]
    if not auction_items:
        return "本月没有拍卖品。"
    item = min(auction_items, key=lambda row: _to_int(row.get("price_min"), 999999))
    price = _to_int(item.get("price_min"), 0)
    if player.spirit_stones < price:
        return f"拍卖会最低起拍为{item['name']}，需要{price}下品灵石，你暂时无力竞价。"
    player.spirit_stones -= price
    player.heishui_market_spent += price
    player.exposure += max(5, price // 200)
    _add_inventory(player, item)
    player.clamp()
    return f"你参与拍卖，拍下{item['name']}，花费{price}下品灵石，暴露度上升。"


def leave_market_check(player: Player) -> str:
    risk = player.exposure + player.tracking_marks * 10
    if risk <= 25:
        return "你压低斗笠离开黑水坊市，没有引人注意。"
    if random.randint(1, 100) <= min(85, risk):
        player.exposure += 3
        player.heart_demon += 1
        player.clamp()
        return "你离开坊市时察觉有人尾随，绕了半个时辰才甩开。暴露度+3，心魔值+1。"
    return "你离开坊市时有人远远盯着，但最终没有跟上来。"


def _condition_value(player: Player, name: str) -> int:
    if name == "has_black_market_password":
        return 1 if player.has_black_market_password else 0
    return _to_int(getattr(player, name, 0))


def _risk_condition_ok(player: Player, condition: Any) -> bool:
    text = str(condition or "").strip()
    if not text:
        return True
    for token in re.split(r"\s+or\s+", text):
        match = re.search(r"([a-zA-Z_]+)\s*>=\s*(-?\d+)", token.strip())
        if match and _condition_value(player, match.group(1)) >= int(match.group(2)):
            return True
    return False


def resolve_monthly_risk_event(player: Player) -> str:
    config = load_config()
    eligible = [event for event in config.risk_events if _risk_condition_ok(player, event.get("condition"))]
    risk_score = (
        player.tracking_marks * 8
        + max(0, player.exposure - 45) // 2
        + max(0, player.karma - 20) // 3
        + max(0, player.demonic_qi - 20) // 3
        + player.heishui_black_market_bought_this_month * 8
        + player.heishui_bloodbag_bought_this_month * 6
        + (6 if player.has_black_market_password or player.heishui_black_intro_count > 0 else 0)
    )
    triggered = ""
    if eligible and risk_score > 0:
        chance = min(55, 4 + risk_score)
        if random.randint(1, 100) <= chance:
            weighted = [(event, _to_int(event.get("weight"), 1) + _to_int(event.get("base_chance"), 0)) for event in eligible]
            event = _weighted_choice(weighted)
            effects = event.get("effects", {})
            effect_notes = _apply_effects_dict(player, effects if isinstance(effects, dict) else {})
            player.heishui_risk_event_count += 1
            triggered = (
                f"黑水坊市风险：{event.get('name')}\n"
                f"{event.get('text')}\n"
                f"影响：{'，'.join(effect_notes) if effect_notes else '无'}"
            )

    player.heishui_black_market_bought_this_month = 0
    player.heishui_bloodbag_bought_this_month = 0
    player.clamp()
    return triggered


def display_shop_stock(player: Player, shop: Dict[str, Any]) -> str:
    config = load_config()
    shop_id = str(shop.get("shop_id"))
    stock = _stock_for_shop(player, shop_id)
    if not stock:
        return "本月暂无库存。"
    lines = [f"{shop['shop_name']}本月库存："]
    for index, entry in enumerate(stock, start=1):
        item = _find_item(config, str(entry.get("item_id")))
        if not item:
            continue
        lines.append(
            f"{index}. {item['name']}｜{entry['price']}灵石｜库存{entry['stock']}｜"
            f"{item.get('category')}｜{item.get('effect_type')}：{item.get('effect_value')}"
        )
    return "\n".join(lines)


def enter_shop(player: Player, shop: Dict[str, Any]) -> str:
    config = load_config()
    print(display_shop_stock(player, shop))
    choice = _read_choice("请选择购买项，输入0返回：")
    if not choice.isdigit() or choice == "0":
        return "你离开柜台。"
    index = int(choice)
    stock = _stock_for_shop(player, str(shop.get("shop_id")))
    if index < 1 or index > len(stock):
        return "没有这件商品。"
    item_id = str(stock[index - 1].get("item_id"))
    item = _find_item(config, item_id)
    if not item:
        return "商品配置异常。"
    return buy_item(player, str(shop.get("shop_id")), item_id)


def display_shop_list(player: Player) -> str:
    config = load_config()
    ensure_market_state(player)
    lines = ["可进入店铺："]
    for index, shop in enumerate(config.shops, start=1):
        unlocked, reason = shop_unlock_reason(player, shop)
        status = "开放" if unlocked else f"锁定：{reason}"
        lines.append(f"{index}. {shop['shop_name']}（{shop['area']}｜{shop['shop_type']}）-{status}")
    events = "、".join(get_active_event_names(player)) or "无"
    lines.append(f"本月行情事件：{events}")
    return "\n".join(lines)


def market_action(player: Player) -> str:
    config = load_config()
    ensure_market_state(player)
    print("黑水坊市：")
    print("1. 查看可用店铺")
    print("2. 进入店铺")
    print("3. 出售普通资源")
    print("4. 聚宝斋寄卖")
    print("5. 珍宝楼拍卖")
    print("6. 月度刷新库存")
    print("0. 离开坊市")
    choice = _read_choice("请选择：")

    if choice == "1":
        return display_shop_list(player)
    if choice == "2":
        print(display_shop_list(player))
        shop_choice = _read_choice("请选择店铺序号：")
        if not shop_choice.isdigit():
            return "你没有进入店铺。"
        index = int(shop_choice)
        if index < 1 or index > len(config.shops):
            return "没有这间店铺。"
        shop = config.shops[index - 1]
        unlocked, reason = shop_unlock_reason(player, shop)
        if not unlocked:
            return f"{shop['shop_name']}暂未开放：{reason}。"
        return enter_shop(player, shop)
    if choice == "3":
        result = sell_basic_resource(player)
        player.clamp()
        return result
    if choice == "4":
        return consign_basic_resource(player) + "\n" + settle_consignments(player)
    if choice == "5":
        return run_simple_auction(player)
    if choice == "6":
        ensure_market_state(player, force=True)
        return "本月黑水坊市库存已刷新。\n" + display_shop_list(player)
    return leave_market_check(player)
