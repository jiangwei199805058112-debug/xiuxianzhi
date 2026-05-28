"""灵田、炼丹炉和轻量装备配置与计算。"""

from __future__ import annotations

import json
from pathlib import Path
import random
from typing import Any, Dict, List, Tuple


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "configs" / "cultivation"
EQUIPMENT_CONFIG_DIR = BASE_DIR / "configs" / "equipment"
EQUIPMENT_SLOTS = ("weapon", "robe", "boots", "talisman")
LEGACY_SLOT_ALIASES = {
    "charm": "talisman",
    "护符": "talisman",
}
EQUIPMENT_ATTRS = (
    "attack_bonus",
    "defense_bonus",
    "speed_bonus",
    "dao_heart_bonus",
    "divine_sense_bonus",
    "cultivation_bonus",
    "alchemy_bonus",
    "stealth_bonus",
    "exposure_bonus",
    "heart_demon_bonus",
    "karma_bonus",
)
EQUIPMENT_ATTR_NAMES = {
    "attack_bonus": "攻击",
    "defense_bonus": "防御",
    "speed_bonus": "身法",
    "dao_heart_bonus": "道心",
    "divine_sense_bonus": "神识",
    "cultivation_bonus": "修炼辅助",
    "alchemy_bonus": "炼丹辅助",
    "stealth_bonus": "隐匿",
    "exposure_bonus": "暴露",
    "heart_demon_bonus": "心魔",
    "karma_bonus": "业力",
}
LEGACY_EFFECT_ALIASES = {
    "attack": "attack_bonus",
    "defense": "defense_bonus",
    "speed": "speed_bonus",
    "dao_heart": "dao_heart_bonus",
    "divine_sense": "divine_sense_bonus",
    "cultivation": "cultivation_bonus",
    "cultivation_speed": "cultivation_bonus",
    "alchemy": "alchemy_bonus",
    "stealth": "stealth_bonus",
    "exposure": "exposure_bonus",
    "heart_demon": "heart_demon_bonus",
    "karma": "karma_bonus",
}
POSITIVE_EQUIPMENT_ATTRS = {
    "attack_bonus",
    "defense_bonus",
    "speed_bonus",
    "dao_heart_bonus",
    "divine_sense_bonus",
    "cultivation_bonus",
    "alchemy_bonus",
    "stealth_bonus",
}
RISK_EQUIPMENT_ATTRS = {"exposure_bonus", "heart_demon_bonus", "karma_bonus"}
QUALITY_NAMES = {
    "common": "普通",
    "uncommon": "良品",
    "rare": "稀有",
    "cursed": "来历不明",
    "reward": "大比奖励",
}
SLOT_NAMES = {
    "weapon": "武器",
    "robe": "法袍",
    "boots": "靴子",
    "talisman": "护符",
}
MATERIAL_NAMES = {
    "material_juqi_grass": "聚气草",
    "material_qingxin_grass": "清心草",
    "material_huangya_grass": "黄芽草",
    "seed_juqi": "聚气草种子",
    "seed_qingxin": "清心草种子",
    "seed_huangya": "黄芽草种子",
}
PLANT_PRIORITY = ("crop_juqi", "crop_qingxin", "crop_huangya")
MAX_FIELD_PLOTS = 3


def _load_json(filename: str) -> Any:
    path = CONFIG_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_crops() -> List[Dict[str, Any]]:
    data = _load_json("spirit_field_crops.json")
    return data if isinstance(data, list) else []


def load_furnaces() -> List[Dict[str, Any]]:
    data = _load_json("alchemy_furnaces.json")
    return data if isinstance(data, list) else []


def _load_json_path(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_equipment_slot(slot: Any) -> str:
    raw_slot = str(slot or "").strip()
    return LEGACY_SLOT_ALIASES.get(raw_slot, raw_slot)


def normalize_equipment_effects(effects: Any) -> Dict[str, int]:
    if not isinstance(effects, dict):
        return {}
    normalized: Dict[str, int] = {}
    for raw_attr, raw_value in effects.items():
        attr = LEGACY_EFFECT_ALIASES.get(str(raw_attr), str(raw_attr))
        if attr not in EQUIPMENT_ATTRS:
            continue
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            continue
        if value:
            normalized[attr] = normalized.get(attr, 0) + value
    return normalized


def _normalize_str_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def normalize_equipment_item(item: Dict[str, Any]) -> Dict[str, Any]:
    item_id = str(item.get("id") or item.get("item_id") or "").strip()
    slot = normalize_equipment_slot(item.get("slot"))
    effects = normalize_equipment_effects(item.get("effects", {}))
    try:
        price = int(item.get("price", 0))
    except (TypeError, ValueError):
        price = 0
    return {
        "id": item_id,
        "item_id": item_id,
        "name": str(item.get("name") or item_id),
        "slot": slot if slot in EQUIPMENT_SLOTS else "talisman",
        "quality": str(item.get("quality") or "common"),
        "price": max(0, price),
        "description": str(item.get("description") or item.get("desc") or ""),
        "desc": str(item.get("description") or item.get("desc") or ""),
        "effects": effects,
        "tags": _normalize_str_list(item.get("tags")),
        "risk_tags": _normalize_str_list(item.get("risk_tags")),
    }


def load_equipment_items() -> List[Dict[str, Any]]:
    new_path = EQUIPMENT_CONFIG_DIR / "equipment_items.json"
    if new_path.exists():
        data = _load_json_path(new_path)
    else:
        data = _load_json("equipment.json")
    raw_items = data if isinstance(data, list) else []
    items = [normalize_equipment_item(item) for item in raw_items if isinstance(item, dict)]
    return [item for item in items if item["item_id"]]


def load_equipment() -> List[Dict[str, Any]]:
    return load_equipment_items()


def load_equipment_sources() -> Dict[str, Dict[str, Any]]:
    path = EQUIPMENT_CONFIG_DIR / "equipment_sources.json"
    if not path.exists():
        return {
            "market_basic": {
                "name": "普通坊市基础装备",
                "items": [
                    {"equipment_id": item["item_id"], "price": item.get("price", 0), "weight": 1}
                    for item in load_equipment_items()
                ],
            }
        }
    data = _load_json_path(path)
    return data if isinstance(data, dict) else {}


def crops_by_id() -> Dict[str, Dict[str, Any]]:
    return {str(crop.get("crop_id")): crop for crop in load_crops()}


def furnaces_by_id() -> Dict[str, Dict[str, Any]]:
    return {str(furnace.get("furnace_id")): furnace for furnace in load_furnaces()}


def equipment_by_id() -> Dict[str, Dict[str, Any]]:
    return {str(item.get("item_id")): item for item in load_equipment_items()}


def get_equipment_by_id(equipment_id: str) -> Dict[str, Any] | None:
    return equipment_by_id().get(str(equipment_id))


def empty_field(plot_id: int) -> Dict[str, Any]:
    return {
        "plot_id": plot_id,
        "crop_id": "",
        "months_left": 0,
        "tended": 0,
        "quality": 0,
        "withered": False,
    }


def ensure_spirit_fields(player: Any) -> None:
    fields = getattr(player, "spirit_fields", None)
    if not isinstance(fields, list) or not fields:
        fields = [empty_field(1)]
    normalized: List[Dict[str, Any]] = []
    for index, field in enumerate(fields[:MAX_FIELD_PLOTS], start=1):
        if not isinstance(field, dict):
            field = {}
        crop_id = str(field.get("crop_id") or "")
        try:
            months_left = int(field.get("months_left", 0))
        except (TypeError, ValueError):
            months_left = 0
        try:
            tended = int(field.get("tended", 0))
        except (TypeError, ValueError):
            tended = 0
        try:
            quality = int(field.get("quality", 0))
        except (TypeError, ValueError):
            quality = 0
        normalized.append(
            {
                "plot_id": index,
                "crop_id": crop_id,
                "months_left": max(0, months_left),
                "tended": max(0, min(tended, 2)),
                "quality": max(0, min(quality, 3)),
                "withered": bool(field.get("withered", False)),
            }
        )
    player.spirit_fields = normalized


def seed_counts_text(player: Any) -> str:
    parts = []
    inventory = getattr(player, "market_inventory", {})
    for key in ("seed_juqi", "seed_qingxin", "seed_huangya"):
        count = int(inventory.get(key, 0))
        if count:
            parts.append(f"{MATERIAL_NAMES[key]}x{count}")
    return "、".join(parts) if parts else "暂无种子"


def material_counts_text(player: Any) -> str:
    parts = []
    inventory = getattr(player, "market_inventory", {})
    for key in ("material_juqi_grass", "material_qingxin_grass", "material_huangya_grass"):
        count = int(inventory.get(key, 0))
        if count:
            parts.append(f"{MATERIAL_NAMES[key]}x{count}")
    return "、".join(parts) if parts else "暂无炼丹材料"


def field_status_text(player: Any) -> str:
    ensure_spirit_fields(player)
    crops = crops_by_id()
    lines = ["灵田状态："]
    for field in player.spirit_fields:
        crop_id = str(field.get("crop_id") or "")
        if not crop_id:
            lines.append(f"{field['plot_id']}. 空闲")
            continue
        crop = crops.get(crop_id, {})
        crop_name = str(crop.get("name", crop_id))
        if field.get("withered"):
            state = "已枯萎，可一键收获时清理"
        elif int(field.get("months_left", 0)) <= 0:
            state = "成熟可收获"
        else:
            state = f"剩余{int(field.get('months_left', 0))}个月"
        tended_text = f"照料{int(field.get('tended', 0))}次"
        quality_text = f"长势+{int(field.get('quality', 0))}"
        lines.append(f"{field['plot_id']}. {crop_name}｜{state}｜{tended_text}｜{quality_text}")
    lines.append(f"种子：{seed_counts_text(player)}")
    lines.append(f"材料：{material_counts_text(player)}")
    return "\n".join(lines)


def buy_seed_pack(player: Any) -> str:
    cost = 4
    if player.spirit_stones < cost:
        return "灵石不足，基础种子包需要4枚灵石。"
    player.spirit_stones -= cost
    inventory = player.market_inventory
    inventory["seed_juqi"] = int(inventory.get("seed_juqi", 0)) + 1
    inventory["seed_qingxin"] = int(inventory.get("seed_qingxin", 0)) + 1
    inventory["seed_huangya"] = int(inventory.get("seed_huangya", 0)) + 1
    player.clamp()
    return "你买下基础种子包，获得聚气草种子x1、清心草种子x1、黄芽草种子x1。"


def grant_starter_seeds(player: Any) -> None:
    inventory = player.market_inventory
    inventory["seed_juqi"] = int(inventory.get("seed_juqi", 0)) + 1
    inventory["seed_huangya"] = int(inventory.get("seed_huangya", 0)) + 1
    player.clamp()


def one_click_plant(player: Any) -> str:
    ensure_spirit_fields(player)
    crops = crops_by_id()
    inventory = player.market_inventory
    empty_fields = [field for field in player.spirit_fields if not field.get("crop_id") and not field.get("withered")]
    if not empty_fields:
        return "没有空闲灵田可种植。"

    planted: List[str] = []
    for field in empty_fields:
        chosen = None
        for crop_id in PLANT_PRIORITY:
            crop = crops.get(crop_id)
            seed_item = str(crop.get("seed_item", "")) if crop else ""
            if seed_item and int(inventory.get(seed_item, 0)) > 0:
                chosen = crop
                break
        if not chosen:
            break
        seed_item = str(chosen["seed_item"])
        inventory[seed_item] = int(inventory.get(seed_item, 0)) - 1
        field["crop_id"] = str(chosen["crop_id"])
        field["months_left"] = int(chosen.get("growth_months", 1))
        field["tended"] = 0
        field["quality"] = 0
        field["withered"] = False
        planted.append(str(chosen["name"]))

    player.clamp()
    if not planted:
        return "没有可用种子，无法一键种植。可先在修炼准备中购买基础种子包。"
    return "一键种植完成：" + "、".join(planted) + "。"


def tend_all_fields(player: Any) -> str:
    ensure_spirit_fields(player)
    targets = [
        field
        for field in player.spirit_fields
        if field.get("crop_id") and not field.get("withered") and int(field.get("months_left", 0)) > 0
    ]
    if not targets:
        return "没有需要照料的未成熟作物。"
    quality_gains = 0
    for field in targets:
        field["tended"] = min(2, int(field.get("tended", 0)) + 1)
        if random.random() < 0.20:
            field["quality"] = min(3, int(field.get("quality", 0)) + 1)
            quality_gains += 1
    player.contribution += 1
    player.npc_affection["沈若兰"] = player.npc_affection.get("沈若兰", 0) + 1
    player.clamp()
    quality_text = f"，其中{quality_gains}块长势略好" if quality_gains else ""
    return f"一键照料完成，共照料{len(targets)}块灵田{quality_text}。"


def _add_market_inventory(player: Any, item_id: str, count: int) -> None:
    if count <= 0:
        return
    player.market_inventory[item_id] = int(player.market_inventory.get(item_id, 0)) + count


def _random_planted_field(player: Any) -> Dict[str, Any] | None:
    ensure_spirit_fields(player)
    planted = [
        field
        for field in player.spirit_fields
        if field.get("crop_id") and not field.get("withered") and int(field.get("months_left", 0)) > 0
    ]
    return random.choice(planted) if planted else None


def _roll_range(value: Any) -> int:
    if isinstance(value, list) and len(value) == 2:
        try:
            low = int(value[0])
            high = int(value[1])
        except (TypeError, ValueError):
            return 0
        return random.randint(low, high)
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def harvest_all_fields(player: Any) -> str:
    ensure_spirit_fields(player)
    crops = crops_by_id()
    totals: Dict[str, int] = {}
    harvested = 0
    cleaned = 0
    for field in player.spirit_fields:
        crop_id = str(field.get("crop_id") or "")
        if field.get("withered"):
            field.update(empty_field(int(field["plot_id"])))
            cleaned += 1
            continue
        if not crop_id or int(field.get("months_left", 0)) > 0:
            continue
        crop = crops.get(crop_id)
        if not crop:
            field.update(empty_field(int(field["plot_id"])))
            continue

        quality = int(field.get("quality", 0))
        tended = int(field.get("tended", 0))
        for item_id, range_value in dict(crop.get("base_yields", {})).items():
            amount = _roll_range(range_value)
            if item_id.startswith("material_") and (quality > 0 or tended > 0) and random.random() < 0.35:
                amount += 1
            if item_id == "herbs":
                player.herbs += amount
            else:
                _add_market_inventory(player, str(item_id), amount)
            if amount:
                totals[str(item_id)] = totals.get(str(item_id), 0) + amount

        aged_chance = int(crop.get("aged_herb_10_chance", 0)) + quality * 2
        if random.randint(1, 100) <= aged_chance:
            player.aged_herbs_10 += 1
            totals["aged_herbs_10"] = totals.get("aged_herbs_10", 0) + 1

        harvested += 1
        player.spirit_field_harvest_count += 1
        field.update(empty_field(int(field["plot_id"])))

    player.clamp()
    if not harvested and cleaned:
        return f"没有成熟作物可收获，已清理枯萎作物{cleaned}块。"
    if not harvested:
        return "没有成熟作物可收获。"

    names = {"herbs": "普通灵草", "aged_herbs_10": "十年份灵草", **MATERIAL_NAMES}
    gain_text = "、".join(f"{names.get(key, key)}x{value}" for key, value in totals.items())
    clean_text = f"，并清理枯萎作物{cleaned}块" if cleaned else ""
    return f"一键收获完成，共收获{harvested}块灵田：{gain_text}{clean_text}。"


def upgrade_spirit_field(player: Any) -> str:
    ensure_spirit_fields(player)
    current = len(player.spirit_fields)
    if current >= MAX_FIELD_PLOTS:
        return "灵田已扩至当前上限3块。"
    if current == 1:
        stone_cost = 16
        herb_cost = 4
        if player.spirit_stones < stone_cost or player.herbs < herb_cost:
            return "升级到2块灵田需要16枚灵石和4株普通灵草。"
        player.spirit_stones -= stone_cost
        player.herbs -= herb_cost
    else:
        stone_cost = 32
        herb_cost = 8
        aged_cost = 1
        if player.spirit_stones < stone_cost or player.herbs < herb_cost or player.aged_herbs_10 < aged_cost:
            return "升级到3块灵田需要32枚灵石、8株普通灵草和1株十年份灵草。"
        player.spirit_stones -= stone_cost
        player.herbs -= herb_cost
        player.aged_herbs_10 -= aged_cost
    player.spirit_fields.append(empty_field(current + 1))
    player.clamp()
    return f"灵田升级完成，当前可种植{len(player.spirit_fields)}块。"


def spirit_field_atmosphere_event(player: Any) -> str:
    ensure_spirit_fields(player)
    active_fields = [
        field
        for field in player.spirit_fields
        if field.get("crop_id") or field.get("withered") or int(field.get("quality", 0)) > 0
    ]
    if not active_fields and int(getattr(player, "spirit_field_harvest_count", 0)) <= 0:
        return ""

    roll = random.randint(1, 100)
    if roll <= 54:
        return random.choice(
            [
                "灵田小记：灵田中灵气微动，几株幼苗叶尖凝露。",
                "灵田小记：今日灵田长势平平，并无异动。",
                "灵田小记：你沿田埂走了一圈，只听见细碎风声。",
                "灵田小记：土中灵气散得很慢，暂时看不出好坏。",
            ]
        )
    if roll <= 68:
        return "灵田小记：昨夜似有虫痕，所幸发现得早，暂未伤到根系。"
    if roll <= 78:
        material = random.choice(("material_juqi_grass", "material_qingxin_grass", "material_huangya_grass"))
        _add_market_inventory(player, material, 1)
        player.clamp()
        return f"灵田小记：你翻土时发现一截残根，勉强还能入药，{MATERIAL_NAMES[material]}+1。"
    if roll <= 88:
        field = _random_planted_field(player)
        if field:
            field["quality"] = min(3, int(field.get("quality", 0)) + 1)
            player.clamp()
            return "灵田小记：灵气在田垄间缓缓聚拢，一处作物长势略好。"
        return "灵田小记：空田里有淡淡灵气游走，暂时还无作物承接。"
    if roll <= 96:
        exposure_gain = random.randint(1, 2)
        player.exposure += exposure_gain
        player.clamp()
        return f"灵田小记：灵田异香外泄，你隐约觉得有人在远处窥探，暴露度+{exposure_gain}。"

    player.exposure += 3
    player.clamp()
    return "灵田小记：夜里灵气忽然外溢，田边似有脚印，暴露度+3。"


def advance_spirit_fields(player: Any) -> str:
    ensure_spirit_fields(player)
    crops = crops_by_id()
    lines: List[str] = []
    for field in player.spirit_fields:
        crop_id = str(field.get("crop_id") or "")
        if not crop_id or field.get("withered") or int(field.get("months_left", 0)) <= 0:
            field["tended"] = 0
            continue
        crop = crops.get(crop_id)
        crop_name = str(crop.get("name", crop_id)) if crop else crop_id
        tended = int(field.get("tended", 0))
        quality = int(field.get("quality", 0))
        wither_chance = max(2, int(crop.get("wither_chance", 10)) - tended * 4 - quality * 2) if crop else 8
        if random.randint(1, 100) <= wither_chance:
            field["withered"] = True
            field["tended"] = 0
            lines.append(f"灵田事件：{crop_name}遭虫害枯萎。")
            continue

        if random.random() < 0.09:
            field["quality"] = min(3, quality + 1)
            lines.append(f"灵田事件：{crop_name}长势良好。")
        elif random.random() < 0.07:
            player.exposure += 1
            lines.append(f"灵田事件：{crop_name}灵气波动，被人多看了几眼。")

        field["months_left"] = max(0, int(field.get("months_left", 0)) - 1)
        if int(field["months_left"]) <= 0:
            lines.append(f"灵田提示：{crop_name}已经成熟。")
        field["tended"] = 0

    atmosphere = spirit_field_atmosphere_event(player)
    if atmosphere:
        lines.append(atmosphere)
    player.clamp()
    return "\n".join(lines)


def current_furnace(player: Any) -> Dict[str, Any]:
    furnaces = furnaces_by_id()
    furnace_id = str(getattr(player, "alchemy_furnace_id", "none") or "none")
    return furnaces.get(furnace_id, furnaces.get("none", {"name": "无专用丹炉", "level": 0}))


def furnace_level(player: Any) -> int:
    return int(current_furnace(player).get("level", 0))


def furnace_status_text(player: Any) -> str:
    furnace = current_furnace(player)
    return (
        f"当前丹炉：{furnace.get('name', '无专用丹炉')}｜等级{int(furnace.get('level', 0))}｜"
        f"成功修正+{int(furnace.get('success_bonus', 0))}｜成丹+{int(furnace.get('pill_bonus', 0))}"
    )


def furnace_shop_text(player: Any) -> str:
    current_id = str(getattr(player, "alchemy_furnace_id", "none") or "none")
    lines = ["炼丹炉："]
    for index, furnace in enumerate(load_furnaces(), start=1):
        mark = "（当前）" if str(furnace.get("furnace_id")) == current_id else ""
        lines.append(
            f"{index}. {furnace.get('name')}{mark}：{int(furnace.get('price', 0))}灵石｜"
            f"等级{int(furnace.get('level', 0))}｜{furnace.get('desc', '')}"
        )
    return "\n".join(lines)


def buy_furnace(player: Any, index: int) -> str:
    furnaces = load_furnaces()
    if index < 1 or index > len(furnaces):
        return "没有这件丹炉。"
    furnace = furnaces[index - 1]
    furnace_id = str(furnace.get("furnace_id"))
    if furnace_id == str(getattr(player, "alchemy_furnace_id", "none") or "none"):
        return f"你已经在使用{furnace.get('name')}。"
    price = int(furnace.get("price", 0))
    if player.spirit_stones < price:
        return f"灵石不足，买不起{furnace.get('name')}。"
    player.spirit_stones -= price
    player.alchemy_furnace_id = furnace_id
    player.clamp()
    return f"你换用{furnace.get('name')}，花费灵石{price}。"


def material_total(player: Any) -> int:
    inventory = getattr(player, "market_inventory", {})
    return sum(int(inventory.get(key, 0)) for key in ("material_juqi_grass", "material_qingxin_grass", "material_huangya_grass"))


def consume_alchemy_materials(player: Any, amount: int) -> Dict[str, int]:
    inventory = player.market_inventory
    consumed: Dict[str, int] = {}
    for key in ("material_juqi_grass", "material_qingxin_grass", "material_huangya_grass"):
        if amount <= 0:
            break
        available = int(inventory.get(key, 0))
        take = min(available, amount)
        if take <= 0:
            continue
        inventory[key] = available - take
        consumed[key] = take
        amount -= take
    player.clamp()
    return consumed


def ensure_equipment(player: Any) -> None:
    inventory = getattr(player, "equipment_inventory", None)
    if isinstance(inventory, list):
        list_inventory: Dict[str, int] = {}
        for item_id in inventory:
            if str(item_id):
                list_inventory[str(item_id)] = list_inventory.get(str(item_id), 0) + 1
        inventory = list_inventory
    if not isinstance(inventory, dict):
        inventory = {}
    clean_inventory: Dict[str, int] = {}
    for key, value in inventory.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            clean_inventory[str(key)] = count
    player.equipment_inventory = clean_inventory

    equipped = getattr(player, "equipped_items", None)
    if not isinstance(equipped, dict):
        equipped = {}
    clean_equipped = {slot: "" for slot in EQUIPMENT_SLOTS}
    for raw_slot, raw_item_id in equipped.items():
        slot = normalize_equipment_slot(raw_slot)
        if slot in clean_equipped and str(raw_item_id or ""):
            clean_equipped[slot] = str(raw_item_id)
    player.equipped_items = clean_equipped

    history = getattr(player, "equipment_history", None)
    if not isinstance(history, list):
        history = []
    clean_history: List[Dict[str, Any]] = []
    for entry in history:
        if not isinstance(entry, dict):
            continue
        item_id = str(entry.get("equipment_id") or entry.get("item_id") or "")
        if not item_id:
            continue
        try:
            count = int(entry.get("count", 1) or 1)
        except (TypeError, ValueError):
            count = 1
        clean_history.append(
            {
                "action": str(entry.get("action") or "gain"),
                "equipment_id": item_id,
                "source": str(entry.get("source") or ""),
                "count": max(1, count),
            }
        )
    player.equipment_history = clean_history[-80:]


def equipment_bonus(player: Any, attr: str) -> int:
    ensure_equipment(player)
    attr = LEGACY_EFFECT_ALIASES.get(str(attr), str(attr))
    items = equipment_by_id()
    total = 0
    for item_id in player.equipped_items.values():
        item = items.get(str(item_id))
        if not item:
            continue
        effects = item.get("effects", {})
        if isinstance(effects, dict):
            total += int(effects.get(attr, 0))
    return total


def get_equipment_effects(equipment_id: str) -> Dict[str, int]:
    item = get_equipment_by_id(str(equipment_id))
    if not item:
        return {}
    effects = item.get("effects", {})
    return dict(effects) if isinstance(effects, dict) else {}


def equipment_effects(player: Any) -> Dict[str, int]:
    return {attr: equipment_bonus(player, attr) for attr in EQUIPMENT_ATTRS}


def get_equipped_effects(player: Any) -> Dict[str, int]:
    return equipment_effects(player)


def calculate_equipment_total_effects(player: Any) -> Dict[str, int]:
    return equipment_effects(player)


def equipment_score(player: Any) -> int:
    effects = equipment_effects(player)
    score = (
        effects["attack_bonus"]
        + effects["defense_bonus"]
        + effects["speed_bonus"]
        + effects["dao_heart_bonus"]
        + effects["divine_sense_bonus"]
        + min(2, max(0, effects["cultivation_bonus"] + effects["alchemy_bonus"] + effects["stealth_bonus"]))
        - max(0, effects["exposure_bonus"])
        - max(0, effects["heart_demon_bonus"])
        - max(0, effects["karma_bonus"])
    )
    return max(0, score)


def equipment_count(player: Any) -> int:
    ensure_equipment(player)
    return sum(player.equipment_inventory.values()) + sum(1 for item_id in player.equipped_items.values() if item_id)


def equipment_slot_count(player: Any) -> int:
    ensure_equipment(player)
    return sum(1 for item_id in player.equipped_items.values() if item_id)


def is_high_risk_equipment(item: Dict[str, Any] | None) -> bool:
    if not item:
        return False
    effects = item.get("effects", {})
    risk_tags = item.get("risk_tags", [])
    risk_values: List[int] = []
    if isinstance(effects, dict):
        for attr in RISK_EQUIPMENT_ATTRS:
            try:
                risk_values.append(int(effects.get(attr, 0)))
            except (TypeError, ValueError):
                risk_values.append(0)
    return (
        str(item.get("quality")) == "cursed"
        or bool(risk_tags)
        or any(value > 0 for value in risk_values)
    )


def high_risk_equipment_count(player: Any) -> int:
    ensure_equipment(player)
    items = equipment_by_id()
    total = 0
    for item_id, count in player.equipment_inventory.items():
        if is_high_risk_equipment(items.get(item_id)):
            total += count
    for item_id in player.equipped_items.values():
        if item_id and is_high_risk_equipment(items.get(item_id)):
            total += 1
    return total


def equipment_acquired_count(player: Any) -> int:
    ensure_equipment(player)
    total = 0
    for entry in getattr(player, "equipment_history", []):
        if str(entry.get("action")) in {"gain", "buy"}:
            total += int(entry.get("count", 1))
    return total


def high_risk_equipment_acquired_count(player: Any) -> int:
    ensure_equipment(player)
    items = equipment_by_id()
    total = 0
    for entry in getattr(player, "equipment_history", []):
        if str(entry.get("action")) in {"gain", "buy"} and is_high_risk_equipment(
            items.get(str(entry.get("equipment_id")))
        ):
            total += int(entry.get("count", 1))
    return total


def format_equipment_effects(effects: Dict[str, int], show_zero: bool = False) -> str:
    parts = []
    for attr in EQUIPMENT_ATTRS:
        value = int(effects.get(attr, 0))
        if value or show_zero:
            parts.append(f"{EQUIPMENT_ATTR_NAMES[attr]}{value:+d}")
    return "、".join(parts) if parts else "无"


def equipment_slot_summary(player: Any) -> str:
    ensure_equipment(player)
    items = equipment_by_id()
    parts = []
    for slot in EQUIPMENT_SLOTS:
        item = items.get(player.equipped_items.get(slot, ""))
        parts.append(f"{SLOT_NAMES[slot]}:{item.get('name') if item else '未装备'}")
    return "｜".join(parts)


def equipment_status_text(player: Any) -> str:
    ensure_equipment(player)
    items = equipment_by_id()
    lines = ["当前装备："]
    for slot in EQUIPMENT_SLOTS:
        item = items.get(player.equipped_items.get(slot, ""))
        if item:
            effects = item.get("effects", {})
            quality = QUALITY_NAMES.get(str(item.get("quality")), str(item.get("quality", "")))
            lines.append(
                f"{SLOT_NAMES[slot]}：{item.get('name')}｜{quality}｜{format_equipment_effects(effects)}"
            )
        else:
            lines.append(f"{SLOT_NAMES[slot]}：当前未装备")
    if player.equipment_inventory:
        inv_text = []
        for item_id, count in player.equipment_inventory.items():
            item = items.get(item_id)
            inv_text.append(f"{item.get('name', item_id) if item else item_id}x{count}")
        lines.append("背包装备：" + "、".join(inv_text))
    else:
        lines.append("背包装备：无")
    lines.append("装备总加成：" + format_equipment_effects(equipment_effects(player)))
    return "\n".join(lines)


def equipment_shop_entries(source_id: str = "market_basic") -> List[Tuple[Dict[str, Any], int, int]]:
    items = equipment_by_id()
    source = load_equipment_sources().get(source_id, {})
    entries = source.get("items", []) if isinstance(source, dict) else []
    result: List[Tuple[Dict[str, Any], int, int]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        item = items.get(str(entry.get("equipment_id")))
        if not item:
            continue
        try:
            price = int(entry.get("price", item.get("price", 0)))
            weight = int(entry.get("weight", 1))
        except (TypeError, ValueError):
            continue
        result.append((item, max(0, price), max(1, weight)))
    return result


def equipment_shop_text(source_id: str = "market_basic") -> str:
    source = load_equipment_sources().get(source_id, {})
    source_name = str(source.get("name", "轻量装备摊")) if isinstance(source, dict) else "轻量装备摊"
    lines = [source_name + "："]
    for index, (item, price, _) in enumerate(equipment_shop_entries(source_id), start=1):
        effects = item.get("effects", {})
        quality = QUALITY_NAMES.get(str(item.get("quality")), str(item.get("quality", "")))
        lines.append(
            f"{index}. {item.get('name')}｜{SLOT_NAMES.get(str(item.get('slot')), item.get('slot'))}｜"
            f"{quality}｜{price}灵石｜{format_equipment_effects(effects)}"
        )
    return "\n".join(lines)


def _record_equipment_history(player: Any, action: str, equipment_id: str, source: str, count: int) -> None:
    history = getattr(player, "equipment_history", None)
    if not isinstance(history, list):
        history = []
    history.append(
        {
            "action": action,
            "equipment_id": str(equipment_id),
            "source": str(source or ""),
            "count": max(1, int(count)),
        }
    )
    player.equipment_history = history[-80:]


def add_equipment_to_inventory(player: Any, equipment_id: str, source: str | None = None, count: int = 1) -> str:
    if count <= 0:
        return ""
    item = equipment_by_id().get(str(equipment_id))
    if not item:
        return ""
    ensure_equipment(player)
    item_id = str(item.get("item_id"))
    player.equipment_inventory[item_id] = int(player.equipment_inventory.get(item_id, 0)) + count
    _record_equipment_history(player, "gain", item_id, source or "", count)
    player.clamp()
    suffix = f"x{count}" if count > 1 else ""
    return f"{item.get('name')}{suffix}"


def buy_equipment(player: Any, index: int, source_id: str = "market_basic") -> str:
    entries = equipment_shop_entries(source_id)
    if index < 1 or index > len(entries):
        return "没有这件装备。"
    item, price, _ = entries[index - 1]
    if player.spirit_stones < price:
        return f"灵石不足，买不起{item.get('name')}。"
    player.spirit_stones -= price
    ensure_equipment(player)
    item_id = str(item.get("item_id"))
    player.equipment_inventory[item_id] = int(player.equipment_inventory.get(item_id, 0)) + 1
    _record_equipment_history(player, "buy", item_id, source_id, 1)
    player.clamp()
    return f"你买下{item.get('name')}，花费灵石{price}。"


def grant_equipment(player: Any, item_id: str, count: int = 1) -> str:
    return add_equipment_to_inventory(player, item_id, source="direct_grant", count=count)


def roll_equipment_from_source(source_id: str) -> str:
    entries = equipment_shop_entries(source_id)
    if not entries:
        return ""
    total = sum(weight for _, _, weight in entries)
    roll = random.randint(1, total)
    cursor = 0
    for item, _, weight in entries:
        cursor += weight
        if roll <= cursor:
            return str(item.get("item_id"))
    return str(entries[-1][0].get("item_id"))


def grant_equipment_from_source(player: Any, source_id: str) -> str:
    item_id = roll_equipment_from_source(source_id)
    if not item_id:
        return ""
    return add_equipment_to_inventory(player, item_id, source=source_id)


def inventory_equipment_choices(player: Any) -> List[Tuple[str, Dict[str, Any]]]:
    ensure_equipment(player)
    items = equipment_by_id()
    choices: List[Tuple[str, Dict[str, Any]]] = []
    for item_id, count in player.equipment_inventory.items():
        item = items.get(item_id)
        if item and count > 0:
            choices.append((item_id, item))
    return choices


def equipment_inventory_text(player: Any) -> str:
    choices = inventory_equipment_choices(player)
    if not choices:
        return "背包中没有可装备的装备。"
    lines = ["可装备物品："]
    for index, (item_id, item) in enumerate(choices, start=1):
        effects = item.get("effects", {})
        quality = QUALITY_NAMES.get(str(item.get("quality")), str(item.get("quality", "")))
        count = int(player.equipment_inventory.get(item_id, 0))
        lines.append(
            f"{index}. {item.get('name')}x{count}｜{SLOT_NAMES.get(str(item.get('slot')), item.get('slot'))}｜"
            f"{quality}｜{format_equipment_effects(effects)}"
        )
    return "\n".join(lines)


def _describe_equipment_line(item: Dict[str, Any] | None) -> str:
    if not item:
        return "当前未装备"
    quality = QUALITY_NAMES.get(str(item.get("quality")), str(item.get("quality", "")))
    return (
        f"{item.get('name')}｜{SLOT_NAMES.get(str(item.get('slot')), item.get('slot'))}｜"
        f"{quality}｜{format_equipment_effects(item.get('effects', {}))}"
    )


def _change_label(attr: str, diff: int) -> str:
    if diff == 0:
        return "无变化"
    if attr in RISK_EQUIPMENT_ATTRS:
        return f"风险上升 {diff:+d}" if diff > 0 else f"风险下降 {diff:+d}"
    return f"提升 {diff:+d}" if diff > 0 else f"降低 {diff:+d}"


def compare_equipment(player: Any, candidate_equipment_id: str) -> Dict[str, Any]:
    ensure_equipment(player)
    items = equipment_by_id()
    candidate = items.get(str(candidate_equipment_id))
    if not candidate:
        return {"error": "装备不存在。"}
    slot = str(candidate.get("slot", ""))
    current = items.get(player.equipped_items.get(slot, ""))
    current_effects = current.get("effects", {}) if current else {}
    candidate_effects = candidate.get("effects", {})
    changes = {}
    for attr in EQUIPMENT_ATTRS:
        current_value = int(current_effects.get(attr, 0)) if isinstance(current_effects, dict) else 0
        candidate_value = int(candidate_effects.get(attr, 0)) if isinstance(candidate_effects, dict) else 0
        changes[attr] = {
            "current": current_value,
            "candidate": candidate_value,
            "diff": candidate_value - current_value,
        }
    return {"slot": slot, "current": current, "candidate": candidate, "changes": changes}


def format_equipment_compare(player: Any, candidate_equipment_id: str) -> str:
    comparison = compare_equipment(player, candidate_equipment_id)
    if comparison.get("error"):
        return str(comparison["error"])
    slot = str(comparison["slot"])
    current = comparison.get("current")
    candidate = comparison.get("candidate")
    lines = [
        f"装备对比：{SLOT_NAMES.get(slot, slot)}",
        "当前装备：",
        f"  {_describe_equipment_line(current if isinstance(current, dict) else None)}",
        "候选装备：",
        f"  {_describe_equipment_line(candidate if isinstance(candidate, dict) else None)}",
        "属性变化：",
    ]
    changes = comparison.get("changes", {})
    if not isinstance(changes, dict):
        changes = {}
    for attr, change in changes.items():
        if not isinstance(change, dict):
            continue
        current_value = int(change.get("current", 0))
        candidate_value = int(change.get("candidate", 0))
        diff = int(change.get("diff", 0))
        lines.append(
            f"  {EQUIPMENT_ATTR_NAMES[attr]}：{current_value:+d} -> {candidate_value:+d}（{_change_label(attr, diff)}）"
        )
    return "\n".join(lines)


def format_equipment_comparison(player: Any, item_id: str) -> str:
    return format_equipment_compare(player, item_id)


def equip_item(player: Any, equipment_id_or_index: Any, include_comparison: bool = True) -> str:
    choices = inventory_equipment_choices(player)
    item_id = ""
    item: Dict[str, Any] | None = None
    if isinstance(equipment_id_or_index, int):
        if equipment_id_or_index < 1 or equipment_id_or_index > len(choices):
            return "没有选择装备。"
        item_id, item = choices[equipment_id_or_index - 1]
    else:
        item_id = str(equipment_id_or_index)
        item = equipment_by_id().get(item_id)
        if not item:
            return "装备不存在。"
        if int(getattr(player, "equipment_inventory", {}).get(item_id, 0)) <= 0:
            return "背包中没有这件装备。"
    if item is None:
        return "装备不存在。"
    slot = str(item.get("slot"))
    current_id = player.equipped_items.get(slot, "")
    if current_id == item_id:
        return f"你已经装备着{item.get('name')}。"
    comparison = format_equipment_compare(player, item_id)
    current_id = player.equipped_items.get(slot, "")
    player.equipment_inventory[item_id] -= 1
    if player.equipment_inventory[item_id] <= 0:
        del player.equipment_inventory[item_id]
    if current_id:
        player.equipment_inventory[current_id] = int(player.equipment_inventory.get(current_id, 0)) + 1
    player.equipped_items[slot] = item_id
    _record_equipment_history(player, "equip", item_id, slot, 1)
    player.clamp()
    prefix = comparison + "\n" if include_comparison else ""
    return prefix + f"已装备：{item.get('name')}。"


def unequip_slot(player: Any, slot: str) -> str:
    ensure_equipment(player)
    normalized_slot = normalize_equipment_slot(slot)
    if normalized_slot not in EQUIPMENT_SLOTS:
        return "没有这个装备槽位。"
    item_id = player.equipped_items.get(normalized_slot, "")
    if not item_id:
        return f"{SLOT_NAMES[normalized_slot]}当前未装备。"
    item = equipment_by_id().get(item_id)
    player.equipped_items[normalized_slot] = ""
    player.equipment_inventory[item_id] = int(player.equipment_inventory.get(item_id, 0)) + 1
    _record_equipment_history(player, "unequip", item_id, normalized_slot, 1)
    player.clamp()
    return f"已卸下{SLOT_NAMES[normalized_slot]}：{item.get('name') if item else item_id}。"
