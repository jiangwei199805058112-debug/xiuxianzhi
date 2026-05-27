"""第一章数值平衡自动模拟工具。"""

from __future__ import annotations

import argparse
import builtins
from contextlib import redirect_stdout
import io
import random
from typing import Dict, Iterable, List, Tuple

from cultivation_assets import equipment_by_id, equipment_count, equipment_score, furnace_level
from data import MARKET_GOODS, NPCS, TOTAL_ACTIONS, VERSION
from growth_system import calculate_breadth, has_insight, mastery_total
from heishui_market import ensure_market_state, load_config, shop_unlock_reason
from player import Player, create_player
from systems import monthly_event, perform_action
from theft_system import THEFT_NEGATIVE_FLAGS
from tournament import run_tournament

DEFAULT_RUNS = 200
DEFAULT_SEED = 20260527
TRACKED_INSIGHTS = [
    "静水深流",
    "法随心动",
    "药理通明",
    "山野老手",
    "族中耳目",
    "妙手无痕",
    "百艺旁通",
    "万法互证",
]

ROUTES: List[Dict[str, object]] = [
    {
        "name": "纯打坐流",
        "weights": [("1", 70), ("legacy_spell_training", 15), ("legacy_investigate", 10), ("legacy_meditate", 5)],
    },
    {
        "name": "古玉瓶炼丹流",
        "weights": [
            ("legacy_spirit_field", 20),
            ("3", 17),
            ("8_field", 10),
            ("8_furnace", 8),
            ("4", 12),
            ("1", 25),
            ("legacy_investigate", 5),
            ("legacy_meditate", 3),
        ],
    },
    {
        "name": "坊市符箓流",
        "weights": [
            ("2", 20),
            ("4", 30),
            ("1", 20),
            ("legacy_spell_training", 15),
            ("legacy_investigate", 10),
            ("legacy_meditate", 5),
        ],
    },
    {
        "name": "魔道炼魂流",
        "weights": [
            ("2", 25),
            ("6", 25),
            ("1", 20),
            ("legacy_spell_training", 15),
            ("legacy_family_work", 10),
            ("legacy_meditate", 5),
        ],
    },
    {
        "name": "均衡流",
        "weights": [
            ("1", 22),
            ("legacy_spirit_field", 13),
            ("2", 14),
            ("4", 14),
            ("legacy_spell_training", 9),
            ("legacy_investigate", 9),
            ("5", 5),
            ("legacy_meditate", 5),
            ("8_field", 4),
            ("8_equip", 5),
        ],
    },
    {
        "name": "黑水投机流",
        "weights": [
            ("4", 42),
            ("2", 24),
            ("legacy_family_work", 14),
            ("1", 10),
            ("legacy_investigate", 5),
            ("legacy_meditate", 5),
        ],
    },
    {
        "name": "盗术投机流",
        "weights": [
            ("8_theft_train", 30),
            ("8_theft_basic", 14),
            ("8_theft_stall", 12),
            ("8_theft_intel", 10),
            ("8_theft_manual", 10),
            ("8_theft_cultivation", 7),
            ("8_theft_high", 4),
            ("1", 6),
            ("2", 4),
            ("legacy_meditate", 3),
        ],
    },
    {
        "name": "随心游玩流",
        "weights": [
            ("1", 5),
            ("2", 10),
            ("legacy_family_work", 10),
            ("legacy_spell_training", 3),
            ("3", 3),
            ("4_normal", 8),
            ("4_heishui", 40),
            ("5", 8),
            ("legacy_meditate", 9),
            ("8_field", 3),
            ("8_equip", 1),
            ("8_theft_train", 1),
            ("8_theft_basic", 2),
            ("8_theft_high", 1),
        ],
    },
    {
        "name": "厚积薄发流",
        "weights": [
            ("1", 24),
            ("legacy_spell_training", 18),
            ("2", 12),
            ("3", 8),
            ("8_field", 10),
            ("legacy_investigate", 12),
            ("5", 8),
            ("4_normal", 4),
            ("legacy_meditate", 4),
        ],
    },
]


def weighted_choice(weighted_actions: Iterable[Tuple[str, int]]) -> str:
    actions = list(weighted_actions)
    total = sum(weight for _, weight in actions)
    roll = random.uniform(0, total)
    cursor = 0.0
    for action, weight in actions:
        cursor += weight
        if roll <= cursor:
            return action
    return actions[-1][0]


class AutoInput:
    def __init__(self, route_name: str, player: Player, action_token: str = "") -> None:
        self.route_name = route_name
        self.player = player
        self.action_token = action_token
        self.entered_heishui = False
        self.target_shop_id = ""
        self.target_market_good = ""

    def __call__(self, prompt: str = "") -> str:
        if "古玉瓶用量" in prompt:
            return self.choose_jade_bottle()
        if "请选择准备事项" in prompt:
            return self.choose_preparation_mode()
        if "请选择灵田操作" in prompt:
            return self.choose_field_preparation_mode()
        if "请选择装备操作" in prompt:
            return self.choose_equipment_mode()
        if "请选择盗术事项" in prompt:
            return self.choose_theft_mode()
        if "请选择处理方式" in prompt:
            return self.choose_theft_resolution()
        if "请选择突破感悟" in prompt:
            return self.choose_breakthrough_insight()
        if "请选择炼丹炉" in prompt:
            return self.choose_furnace()
        if "请选择购买装备" in prompt:
            return self.choose_equipment_purchase()
        if "请选择装备编号" in prompt:
            return self.choose_equipment_to_wear()
        if "请选择商品" in prompt:
            return self.choose_market_good()
        if "请选择出售项" in prompt:
            return self.choose_herb_sale()
        if "请选择对象" in prompt:
            return self.choose_npc()
        if "请选择店铺序号" in prompt:
            return self.choose_heishui_shop()
        if "请选择购买项" in prompt:
            return self.choose_heishui_purchase()
        if "请选择" in prompt:
            return self.choose_market_mode()
        return ""

    def choose_preparation_mode(self) -> str:
        if self.action_token == "8_insight":
            return "5"
        if self.action_token.startswith("8_theft"):
            return "4"
        if self.action_token == "8_furnace":
            return "2"
        if self.action_token == "8_equip":
            return "3"
        if self.action_token == "8_field":
            if (
                self.route_name == "古玉瓶炼丹流"
                and furnace_level(self.player) < 1
                and self.player.spirit_stones >= 8
                and random.random() < 0.55
            ):
                return "2"
            return "1"
        if self.route_name == "古玉瓶炼丹流":
            return "1"
        if self.route_name == "均衡流" and random.random() < 0.45:
            return "1"
        if self.route_name == "随心游玩流" and random.random() < 0.55:
            return "1"
        return "6"

    def choose_breakthrough_insight(self) -> str:
        if self.route_name == "厚积薄发流":
            if self.player.foundation < 50:
                return "1"
            needs = [
                ("combat_mastery", "3"),
                ("spirit_field_mastery", "6"),
                ("intel_mastery", "7"),
                ("social_mastery", "8"),
                ("alchemy_mastery", "4"),
                ("herb_mastery", "5"),
                ("cultivation_mastery", "2"),
            ]
            needs.sort(key=lambda item: getattr(self.player, item[0]))
            for attr, choice in needs:
                if getattr(self.player, attr) < 26:
                    return choice
            return "1"
        if self.route_name == "盗术投机流":
            return "9" if self.player.theft_skill < 75 else weighted_choice([("9", 5), ("7", 2), ("3", 2), ("1", 1)])
        if self.route_name == "魔道炼魂流":
            return weighted_choice([("10", 5), ("3", 3), ("1", 2)])
        if self.route_name == "古玉瓶炼丹流":
            return weighted_choice([("4", 5), ("6", 3), ("2", 2)])
        if self.route_name == "均衡流":
            return weighted_choice([("1", 3), ("2", 2), ("3", 2), ("7", 2), ("8", 1)])
        if self.route_name == "随心游玩流":
            return weighted_choice([("1", 3), ("2", 2), ("3", 2), ("4", 1), ("7", 1), ("9", 1)])
        return weighted_choice([("1", 4), ("2", 3), ("3", 2), ("7", 1)])

    def choose_field_preparation_mode(self) -> str:
        fields = self.player.spirit_fields
        has_mature = any(
            field.get("crop_id") and not field.get("withered") and int(field.get("months_left", 0)) <= 0
            for field in fields
        )
        has_withered = any(field.get("withered") for field in fields)
        has_empty = any(not field.get("crop_id") and not field.get("withered") for field in fields)
        has_growing = any(
            field.get("crop_id") and not field.get("withered") and int(field.get("months_left", 0)) > 0
            for field in fields
        )
        has_seeds = any(
            int(self.player.market_inventory.get(key, 0)) > 0
            for key in ("seed_juqi", "seed_qingxin", "seed_huangya")
        )

        if has_mature or has_withered:
            return "4"
        if self.route_name == "古玉瓶炼丹流":
            if (
                len(fields) == 1
                and self.player.month <= 7
                and self.player.spirit_stones >= 18
                and self.player.herbs >= 5
                and random.random() < 0.22
            ):
                return "5"
            if has_empty and has_seeds:
                return "2"
            if has_empty and not has_seeds and self.player.spirit_stones >= 4:
                return "6"
            if has_growing:
                return "3"
            return "1"

        if has_empty and has_seeds:
            return "2"
        if has_growing and random.random() < 0.55:
            return "3"
        if has_empty and not has_seeds and self.player.spirit_stones >= 12 and random.random() < 0.45:
            return "6"
        return "1"

    def choose_equipment_mode(self) -> str:
        if self.player.equipment_inventory and random.random() < 0.55:
            return "3"
        if self.player.spirit_stones >= 8:
            return "2"
        return "1"

    def choose_furnace(self) -> str:
        level = furnace_level(self.player)
        stones = self.player.spirit_stones
        if self.route_name == "古玉瓶炼丹流":
            if level < 1 and stones >= 8:
                return "2"
            if level < 2 and stones >= 28:
                return "3"
            if level < 3 and stones >= 54 and self.player.month <= 8 and random.random() < 0.25:
                return "4"
            return "1"
        if stones >= 28 and level < 2 and random.random() < 0.35:
            return "3"
        if stones >= 8 and level < 1:
            return "2"
        return "1"

    def choose_equipment_purchase(self) -> str:
        items = list(equipment_by_id().values())
        candidates: List[Tuple[str, int]] = []
        for index, item in enumerate(items, start=1):
            price = int(item.get("price", 0))
            item_id = str(item.get("item_id"))
            slot = str(item.get("slot"))
            already_has = int(self.player.equipment_inventory.get(item_id, 0)) > 0
            already_equipped = self.player.equipped_items.get(slot) == item_id
            if self.player.spirit_stones < price or already_has or already_equipped:
                continue
            weight = 8
            if self.route_name == "均衡流":
                weight = 10 if price <= 16 else 3
            if self.route_name == "随心游玩流":
                weight = 8 if price <= 18 else 2
            candidates.append((str(index), weight))
        if not candidates:
            return "0"
        return weighted_choice(candidates)

    def choose_equipment_to_wear(self) -> str:
        if not self.player.equipment_inventory:
            return "0"
        return "1"

    def choose_theft_mode(self) -> str:
        token_map = {
            "8_theft_train": "1",
            "8_theft_basic": "2",
            "8_theft_stall": "3",
            "8_theft_intel": "4",
            "8_theft_manual": "5",
            "8_theft_cultivation": "6",
        }
        if self.action_token in token_map:
            return token_map[self.action_token]
        if self.action_token == "8_theft_high":
            skill = self.player.theft_skill
            if skill >= 95 and self.player.stolen_inheritance_count == 0 and random.random() < 0.10:
                return "11"
            if skill >= 80:
                return weighted_choice([("9", 4), ("10", 3), ("7", 5), ("8", 5), ("6", 8), ("5", 8)])
            if skill >= 65:
                return weighted_choice([("7", 5), ("8", 4), ("6", 8), ("5", 8), ("4", 5)])
            if skill >= 45:
                return weighted_choice([("6", 8), ("5", 8), ("4", 5), ("3", 4)])
            if skill >= 25:
                return weighted_choice([("5", 8), ("4", 6), ("3", 4), ("2", 3)])
            if skill >= 10:
                return weighted_choice([("4", 5), ("3", 5), ("2", 4), ("1", 4)])
            return weighted_choice([("1", 7), ("2", 3)])
        if self.route_name == "盗术投机流":
            return "1" if self.player.theft_skill < 12 else "2"
        if self.route_name == "随心游玩流":
            if self.player.theft_skill < 8:
                return "1" if random.random() < 0.45 else "2"
            if self.player.theft_skill >= 45 and random.random() < 0.04:
                return "6"
            if self.player.theft_skill >= 25 and random.random() < 0.12:
                return "5"
            if self.player.theft_skill >= 10 and random.random() < 0.35:
                return random.choice(["3", "4"])
            return "2"
        return "0"

    def choose_theft_resolution(self) -> str:
        if self.route_name == "盗术投机流":
            if self.player.spirit_stones >= 10:
                return "1" if random.random() < 0.78 else "2"
            if self.player.spirit_stones >= 4:
                return "1" if random.random() < 0.52 else ("3" if random.random() < 0.35 else "2")
            return "3" if random.random() < 0.52 else "2"
        if self.route_name == "魔道炼魂流":
            return weighted_choice([("2", 5), ("3", 4), ("1", 1)])
        if self.route_name == "随心游玩流":
            if self.player.spirit_stones >= 8:
                return weighted_choice([("1", 7), ("2", 2), ("3", 1)])
            return weighted_choice([("1", 4), ("2", 3), ("3", 2)])
        return "1" if self.player.spirit_stones >= 6 else "2"

    def choose_jade_bottle(self) -> str:
        if self.player.exposure > 60:
            return "0"
        if self.player.exposure < 40 and self.player.spirit_stones >= 2 and random.random() < 0.35:
            return "2"
        if self.player.spirit_stones >= 1:
            return "1"
        return "0"

    def choose_market_mode(self) -> str:
        if self.route_name == "随心游玩流":
            return self.choose_casual_market_mode()
        if self.route_name == "黑水投机流":
            if not self.entered_heishui:
                needs_entry_fund = not (
                    self.player.has_black_market_password or self.player.black_market_clue > 0
                )
                target_stones = 18 if needs_entry_fund else 8
                if not needs_entry_fund and self.player.heishui_black_market_purchase_count == 0:
                    target_stones = 24
                if self.player.heishui_purchase_count >= 2 and self.player.heishui_blindbox_purchase_count == 0:
                    target_stones = max(target_stones, 24)
                if self.player.spirit_stones < target_stones and (
                    self.player.aged_herbs_30 > 0 or self.player.aged_herbs_10 > 0 or self.player.herbs > 4
                ):
                    return "B"
                self.entered_heishui = True
                return "D"
            return self.choose_heishui_mode()
        if self.route_name == "古玉瓶炼丹流":
            aged_total = self.player.aged_herbs_30 + self.player.aged_herbs_10
            if aged_total > 0 and (self.player.spirit_stones < 16 or aged_total > 6):
                return "B"
            return "A" if self.choose_market_good() != "0" else "C"
        if self.route_name == "厚积薄发流":
            return "F" if random.random() < 0.70 else "C"
        if self.route_name in {"坊市符箓流", "均衡流"}:
            return "A" if self.choose_market_good() != "0" else "C"
        return "C"

    def choose_casual_market_mode(self) -> str:
        if self.action_token == "4_heishui":
            if self.is_casual_high_risk() and random.random() < 0.60:
                return "F"
            if not self.entered_heishui:
                self.entered_heishui = True
                return "D"
            return self.choose_heishui_mode()

        if self.player.spirit_stones <= 20 and (
            self.player.aged_herbs_30 > 0
            or self.player.aged_herbs_10 > 0
            or self.player.herbs > 4
        ) and random.random() < 0.74:
            return "B"

        self.target_market_good = self.choose_casual_market_good()
        if self.target_market_good != "0" and random.random() < self.casual_buy_chance():
            return "A"
        if random.random() < 0.55:
            return "C"
        return "F"

    def casual_buy_chance(self) -> float:
        chance = 0.45
        if self.is_tournament_near():
            chance += 0.22
        if self.is_casual_high_risk():
            chance -= 0.10
        return max(0.20, min(chance, 0.85))

    def choose_casual_market_good(self) -> str:
        if self.player.spirit_stones < 8:
            return "0"
        preferred_weights = {
            "聚气散": 14,
            "回春丹": 6,
            "清心丸": 5,
            "护身符": 8,
            "火弹符": 8,
            "避火符": 5,
            "破甲符": 5,
            "坊市情报": 8,
            "黑市线索": 4,
        }
        if self.player.hp < self.player.max_hp * 0.55:
            preferred_weights["回春丹"] += 8
        if self.player.heart_demon >= 12:
            preferred_weights["清心丸"] += 10
        if self.is_tournament_near():
            for name in ("护身符", "火弹符", "避火符", "破甲符", "坊市情报", "聚气散"):
                preferred_weights[name] += 6

        candidates: List[Tuple[str, int]] = []
        for index, good in enumerate(MARKET_GOODS, start=1):
            name = str(good["name"])
            price = int(good["price"])
            if name in preferred_weights and self.player.spirit_stones >= price:
                candidates.append((str(index), preferred_weights[name]))
        if not candidates:
            return "0"
        return weighted_choice(candidates)

    def choose_heishui_mode(self) -> str:
        if self.route_name == "随心游玩流":
            return self.choose_casual_heishui_mode()

        config = load_config()
        ensure_market_state(self.player)
        heishi = next((shop for shop in config.shops if shop.get("shop_id") == "shop_heishi"), None)
        heishi_open = bool(heishi and shop_unlock_reason(self.player, heishi)[0])
        stones = self.player.spirit_stones
        if stones < 8:
            return "1"
        if heishi_open and self.player.heishui_black_market_purchase_count == 0 and stones >= 12:
            self.target_shop_id = "shop_heishi"
        elif self.player.heishui_blindbox_purchase_count == 0 and stones >= 24 and random.random() < 0.45:
            self.target_shop_id = "shop_tanwei"
        elif (not heishi_open or self.player.heishui_intel_purchase_count < 2) and stones >= 8:
            self.target_shop_id = "shop_tianji"
        elif heishi_open and stones >= 12 and random.random() < 0.35:
            self.target_shop_id = "shop_heishi"
        elif stones >= 24 and random.random() < 0.30:
            self.target_shop_id = "shop_tanwei"
        elif stones >= 8 and random.random() < 0.25:
            self.target_shop_id = "shop_fengyue"
        else:
            self.target_shop_id = "shop_tianji"
        return "2"

    def choose_casual_heishui_mode(self) -> str:
        if (
            self.player.heishui_blindbox_purchase_count == 0
            and 12 <= self.player.spirit_stones < 22
            and (
                self.player.aged_herbs_30 > 0
                or self.player.aged_herbs_10 > 0
                or self.player.herbs > 3
            )
            and random.random() < 0.70
        ):
            return "3"
        if (
            self.player.heishui_blindbox_purchase_count == 0
            and 10 <= self.player.spirit_stones < 22
            and random.random() < 0.30
        ):
            return "1"
        if 16 <= self.player.spirit_stones < 22 and (
            self.player.aged_herbs_30 > 0
            or self.player.aged_herbs_10 > 0
            or self.player.herbs > 3
        ) and random.random() < 0.60:
            return "3"
        if self.player.spirit_stones < 8 and (
            self.player.aged_herbs_30 > 0
            or self.player.aged_herbs_10 > 0
            or self.player.herbs > 4
        ) and random.random() < 0.55:
            return "3"
        if self.player.spirit_stones < 6:
            return "1"
        if self.is_casual_high_risk():
            if random.random() < 0.60:
                return "0"
            if random.random() < 0.70:
                return "1"
        if random.random() < 0.08:
            return "1"

        self.target_shop_id = self.choose_casual_heishui_shop()
        return "2" if self.target_shop_id else "0"

    def choose_casual_heishui_shop(self) -> str:
        config = load_config()
        ensure_market_state(self.player)
        shop_weights: List[Tuple[str, int]] = [
            ("shop_baicao", 8),
            ("shop_juling", 8),
            ("shop_tianji", 28),
            ("shop_tanwei", 50),
            ("shop_fengyue", 11),
        ]
        if self.is_tournament_near():
            shop_weights = [
                ("shop_baicao", 18),
                ("shop_juling", 18),
                ("shop_tianji", 28),
                ("shop_tanwei", 32),
                ("shop_fengyue", 12),
            ]
        if self.is_casual_high_risk():
            shop_weights = [
                ("shop_tianji", 10),
                ("shop_fengyue", 28),
                ("shop_tanwei", 2),
            ]

        heishi = next((shop for shop in config.shops if shop.get("shop_id") == "shop_heishi"), None)
        if heishi and shop_unlock_reason(self.player, heishi)[0] and not self.is_casual_high_risk():
            shop_weights.append(("shop_heishi", 16))

        unlocked_ids = {
            str(shop.get("shop_id"))
            for shop in config.shops
            if shop_unlock_reason(self.player, shop)[0]
        }
        affordable_ids = set()
        for shop_id, stock in self.player.heishui_market_stock.items():
            if any(self.player.spirit_stones >= int(entry.get("price", 0)) for entry in stock):
                affordable_ids.add(str(shop_id))

        candidates = [
            (shop_id, weight)
            for shop_id, weight in shop_weights
            if shop_id in unlocked_ids and shop_id in affordable_ids
        ]
        if not candidates:
            candidates = [(shop_id, weight) for shop_id, weight in shop_weights if shop_id in unlocked_ids]
        if not candidates:
            return ""
        if not self.is_casual_high_risk() and self.player.spirit_stones >= 18:
            tanwei_affordable = any(shop_id == "shop_tanwei" for shop_id, _ in candidates)
            tanwei_chance = 0.95 if self.player.heishui_blindbox_purchase_count == 0 else 0.65
            if tanwei_affordable and random.random() < tanwei_chance:
                return "shop_tanwei"
        return weighted_choice(candidates)

    def choose_heishui_shop(self) -> str:
        config = load_config()
        if not self.target_shop_id:
            self.target_shop_id = "shop_tianji"
        for index, shop in enumerate(config.shops, start=1):
            if shop.get("shop_id") == self.target_shop_id:
                return str(index)
        return "6"

    def choose_heishui_purchase(self) -> str:
        if self.route_name == "随心游玩流":
            return self.choose_casual_heishui_purchase()

        config = load_config()
        ensure_market_state(self.player)
        priorities = {
            "shop_tianji": ["黑市商人引荐", "黑市暗号线索", "百药山灵草线索", "大比对手情报", "坊市行情消息"],
            "shop_tanwei": ["沾血的无名储物袋", "染尘旧储物袋"],
            "shop_heishi": ["来历不明的聚气丹", "残缺魔修手札", "假身份木牌", "破损阵盘"],
            "shop_fengyue": ["打听小道消息", "听曲静心", "结识风月楼管事"],
        }
        items_by_id = {str(item.get("item_id")): item for item in config.items}
        stock = self.player.heishui_market_stock.get(self.target_shop_id, [])
        wanted_names = priorities.get(self.target_shop_id, [])
        for wanted in wanted_names:
            for index, entry in enumerate(stock, start=1):
                item = items_by_id.get(str(entry.get("item_id")))
                if item and item.get("name") == wanted and self.player.spirit_stones >= int(entry.get("price", 0)):
                    return str(index)
        for index, entry in enumerate(stock, start=1):
            if self.player.spirit_stones >= int(entry.get("price", 0)):
                return str(index)
        return "0"

    def choose_casual_heishui_purchase(self) -> str:
        config = load_config()
        ensure_market_state(self.player)
        items_by_id = {str(item.get("item_id")): item for item in config.items}
        stock = self.player.heishui_market_stock.get(self.target_shop_id, [])
        name_weights = {
            "坊市行情消息": 26,
            "百药山灵草线索": 24,
            "大比对手情报": 18,
            "黑市暗号线索": 50,
            "听曲静心": 16,
            "打听小道消息": 22,
            "染尘旧储物袋": 80,
            "赌石": 8,
            "辟谷丹": 4,
            "回春散": 8,
            "聚气丹": 8,
            "回灵丹": 5,
            "火球符": 9,
            "金钟符": 9,
            "神行符": 7,
        }
        if self.is_tournament_near():
            for name in ("大比对手情报", "坊市行情消息", "聚气丹", "回春散", "火球符", "金钟符", "神行符"):
                name_weights[name] += 8
        if self.is_casual_high_risk():
            for name in ("黑市暗号线索", "染尘旧储物袋"):
                name_weights[name] = 1
            name_weights["赌石"] = 1
            name_weights["听曲静心"] += 12

        candidates: List[Tuple[str, int]] = []
        for index, entry in enumerate(stock, start=1):
            price = int(entry.get("price", 0))
            if self.player.spirit_stones < price:
                continue
            item = items_by_id.get(str(entry.get("item_id")))
            if not item:
                continue
            category = str(item.get("category"))
            name = str(item.get("name"))
            weight = name_weights.get(name, 0)
            if category == "盲盒" and name != "染尘旧储物袋":
                weight = max(weight, 4)
            if self.target_shop_id == "shop_heishi":
                weight = 8 if not self.is_casual_high_risk() else 0
            if weight > 0:
                candidates.append((str(index), weight))

        buy_chance = 0.86
        if self.is_tournament_near():
            buy_chance += 0.04
        if self.is_casual_high_risk():
            buy_chance -= 0.22
        if self.target_shop_id == "shop_tanwei":
            buy_chance -= 0.02

        if candidates and random.random() < max(0.35, min(buy_chance, 0.88)):
            return weighted_choice(candidates)
        affordable = [
            (str(index), 1)
            for index, entry in enumerate(stock, start=1)
            if self.player.spirit_stones >= int(entry.get("price", 0))
            and items_by_id.get(str(entry.get("item_id")), {}).get("name") in name_weights
        ]
        if affordable and random.random() < 0.18:
            return weighted_choice(affordable)
        return "0"

    def choose_market_good(self) -> str:
        if self.route_name == "随心游玩流":
            if self.target_market_good:
                target = self.target_market_good
                self.target_market_good = ""
                return target
            return self.choose_casual_market_good()

        stones = self.player.spirit_stones
        if self.route_name == "古玉瓶炼丹流":
            if self.player.alchemy_furnace_id == "none" and stones >= 8:
                return "0"
            if furnace_level(self.player) < 2 and 20 <= stones < 30:
                return "0"
            if self.player.heart_demon >= 10 and stones >= 22:
                return "6"
            if stones >= 20:
                return "4"
            if self.player.heart_demon >= 5 and stones >= 22:
                return "6"
            return "0"
        if self.route_name == "坊市符箓流":
            if self.player.talisman_guard < 1 and stones >= 40:
                return "7"
            if self.player.talisman_fire < 1 and stones >= 36:
                return "8"
            if stones >= 18:
                return "11"
            return "0"
        if self.route_name == "均衡流":
            if self.player.intelligence < 10 and stones >= 18:
                return "11"
            if stones >= 20:
                return "4"
            return "0"
        return "0"

    def choose_herb_sale(self) -> str:
        if self.route_name == "随心游玩流":
            if self.player.aged_herbs_30 > 0:
                return "3"
            if self.player.aged_herbs_10 > 0:
                return "2"
            if self.player.herbs > 3:
                return "1"
            return "0"
        if self.player.aged_herbs_30 > 0:
            return "3"
        if self.player.aged_herbs_10 > 0:
            return "2"
        if self.player.herbs > 6:
            return "1"
        return "0"

    def choose_npc(self) -> str:
        if self.route_name == "随心游玩流":
            return str(random.randint(1, len(NPCS)))
        if self.player.npc_affection.get("沈若兰", 0) < 35:
            return "1"
        if self.player.npc_affection.get("沈霜", 0) < 25:
            return "5"
        return "3"

    def is_tournament_near(self) -> bool:
        return self.player.month >= 10

    def is_casual_high_risk(self) -> bool:
        return (
            self.player.exposure >= 55
            or self.player.heart_demon >= 35
            or self.player.demonic_qi >= 25
            or self.player.karma >= 25
            or self.player.tracking_marks > 0
            or self.player.heishui_risk_event_count > 0
            or self.player.enemy_count >= 3
            or self.player.reputation <= -8
        )


def choose_route_action(route: Dict[str, object], player: Player) -> str:
    if player.breakthrough_insight_pending > 0:
        return "8_insight"

    if str(route["name"]) == "厚积薄发流":
        if player.foundation < 82 and random.random() < 0.32:
            return weighted_choice([("5", 35), ("8_field", 30), ("legacy_meditate", 20), ("1", 15)])
        needs = [
            ("combat_mastery", "legacy_spell_training", 30),
            ("herb_mastery", "2", 30),
            ("intel_mastery", "legacy_investigate", 30),
            ("spirit_field_mastery", "8_field", 28),
            ("social_mastery", "5", 28),
            ("alchemy_mastery", "3", 26),
            ("market_mastery", "4_normal", 20),
            ("cultivation_mastery", "legacy_meditate", 42),
        ]
        low_actions = [(action, threshold - getattr(player, attr)) for attr, action, threshold in needs if getattr(player, attr) < threshold]
        if low_actions and random.random() < 0.88:
            low_actions.sort(key=lambda item: item[1], reverse=True)
            return weighted_choice([(action, max(5, gap)) for action, gap in low_actions[:5]])
        if player.foundation < 88 and random.random() < 0.34:
            return weighted_choice([("5", 35), ("8_field", 30), ("legacy_meditate", 20), ("1", 15)])

    if str(route["name"]) == "盗术投机流":
        theft_risk = (
            player.exposure >= 50
            or player.karma >= 35
            or player.enemy_count >= 2
            or player.reputation <= -6
            or player.hp < player.max_hp * 0.35
        )
        if theft_risk and random.random() < 0.55:
            return weighted_choice([("legacy_meditate", 48), ("1", 32), ("2", 12), ("8_theft_train", 8)])
        skill = player.theft_skill
        if skill < 10:
            return weighted_choice(
                [
                    ("8_theft_train", 70),
                    ("8_theft_basic", 15),
                    ("1", 10),
                    ("2", 3),
                    ("legacy_meditate", 2),
                ]
            )
        if skill < 25:
            return weighted_choice(
                [
                    ("8_theft_train", 45),
                    ("8_theft_basic", 10),
                    ("8_theft_stall", 12),
                    ("8_theft_intel", 10),
                    ("1", 12),
                    ("2", 4),
                    ("legacy_meditate", 7),
                ]
            )
        if skill < 45:
            return weighted_choice(
                [
                    ("8_theft_train", 30),
                    ("8_theft_manual", 12),
                    ("8_theft_intel", 10),
                    ("8_theft_stall", 8),
                    ("8_theft_basic", 5),
                    ("1", 20),
                    ("2", 5),
                    ("legacy_meditate", 10),
                ]
            )
        if skill < 65:
            return weighted_choice(
                [
                    ("8_theft_train", 18),
                    ("8_theft_cultivation", 8),
                    ("8_theft_manual", 10),
                    ("8_theft_intel", 8),
                    ("8_theft_stall", 6),
                    ("1", 25),
                    ("2", 7),
                    ("legacy_meditate", 18),
                ]
            )
        if skill < 80:
            return weighted_choice(
                [
                    ("8_theft_train", 14),
                    ("8_theft_cultivation", 7),
                    ("8_theft_manual", 8),
                    ("8_theft_high", 5),
                    ("8_theft_intel", 6),
                    ("1", 26),
                    ("2", 8),
                    ("legacy_meditate", 26),
                ]
            )
        high_weights = [
            ("8_theft_train", 10),
            ("8_theft_cultivation", 5),
            ("8_theft_manual", 6),
            ("8_theft_high", 5),
            ("8_theft_intel", 5),
            ("1", 28),
            ("2", 8),
            ("legacy_meditate", 33),
        ]
        if skill >= 95 and player.stolen_inheritance_count == 0:
            high_weights.append(("8_theft_high", 1))
        return weighted_choice(high_weights)

    if str(route["name"]) == "随心游玩流":
        high_risk = (
            player.exposure >= 55
            or player.heart_demon >= 35
            or player.demonic_qi >= 25
            or player.karma >= 25
            or player.tracking_marks > 0
            or player.heishui_risk_event_count > 0
            or player.enemy_count >= 3
            or player.reputation <= -8
        )
        if high_risk and random.random() < 0.35:
            return "legacy_meditate"
        if player.hp < player.max_hp * 0.35 and random.random() < 0.25:
            return "legacy_meditate"

    action = weighted_choice(route["weights"])  # type: ignore[arg-type]
    if str(route["name"]) == "随心游玩流" and high_risk and action == "4_heishui" and random.random() < 0.65:
        return "legacy_meditate" if random.random() < 0.60 else "4_normal"
    if action == "6" and not player.has_soul_banner:
        return "2" if random.random() < 0.65 else "1"
    return action


def action_choice_from_token(action_token: str) -> str:
    if action_token in {"4_normal", "4_heishui"}:
        return "4"
    if action_token.startswith("8_"):
        return "8"
    return action_token


def risk_score(player: Player) -> int:
    return (
        player.exposure
        + player.heart_demon
        + player.demonic_qi
        + player.karma
        + player.tracking_marks * 8
        + player.heishui_risk_event_count * 10
        + player.enemy_count * 6
        + max(0, -player.reputation) * 2
    )


def run_single_game(route: Dict[str, object], index: int) -> Dict[str, object]:
    route_name = str(route["name"])
    player = create_player(f"{route_name}{index}")
    while not player.finished:
        action_token = choose_route_action(route, player)
        action = action_choice_from_token(action_token)
        auto_input = AutoInput(route_name, player, action_token)
        old_input = builtins.input
        try:
            builtins.input = auto_input
            with redirect_stdout(io.StringIO()):
                before = player.total_actions
                perform_action(player, action)
                if player.total_actions == before and not bool(getattr(player, "_last_action_waived", False)):
                    player.advance_action()
                if player.total_actions % 3 == 0 and not player.finished:
                    monthly_event(player)
        finally:
            builtins.input = old_input

    result = run_tournament(player)
    result_flags = {str(flag) for flag in result["flags"]}
    return {
        "rank": int(result["rank"]),
        "top_ten": bool(result["top_ten"]),
        "top_three": int(result["rank"]) <= 3,
        "first": int(result["rank"]) == 1,
        "total": int(result["total"]),
        "realm_level": player.realm_level,
        "cultivation_progress": player.cultivation_progress,
        "exposure": player.exposure,
        "heart_demon": player.heart_demon,
        "demonic_qi": player.demonic_qi,
        "karma": player.karma,
        "spirit_stones": player.spirit_stones,
        "herbs": player.herbs,
        "aged_herbs_10": player.aged_herbs_10,
        "aged_herbs_30": player.aged_herbs_30,
        "intelligence": player.intelligence,
        "talisman_bonus": int(result.get("talisman_bonus", 0)),
        "risk_score": risk_score(player),
        "has_jade_bottle": player.has_jade_bottle,
        "has_soul_banner": player.has_soul_banner,
        "magic_flag": "魔影伏身" in result_flags,
        "jade_flag": "玉瓶生疑" in result_flags,
        "theft_negative_flag": bool(result_flags & THEFT_NEGATIVE_FLAGS),
        "high_risk": (
            player.exposure >= 70
            or player.heart_demon >= 60
            or player.demonic_qi >= 45
            or player.karma >= 35
            or player.tracking_marks >= 2
            or player.heishui_risk_event_count >= 2
            or "魔影伏身" in result_flags
            or "玉瓶生疑" in result_flags
        ),
        "heishui_spent": player.heishui_market_spent,
        "heishui_purchase_count": player.heishui_purchase_count,
        "heishui_intel_purchase_count": player.heishui_intel_purchase_count,
        "heishui_black_market_purchase_count": player.heishui_black_market_purchase_count,
        "heishui_blindbox_purchase_count": player.heishui_blindbox_purchase_count,
        "tracking_marks": player.tracking_marks,
        "heishui_risk_event_count": player.heishui_risk_event_count,
        "heishui_blindbox_net": player.heishui_blindbox_net,
        "spirit_field_harvest_count": player.spirit_field_harvest_count,
        "furnace_level": furnace_level(player),
        "equipment_count": equipment_count(player),
        "equipment_score": equipment_score(player),
        "foundation": player.foundation,
        "breadth": calculate_breadth(player),
        "mastery_total": mastery_total(player),
        "unlocked_insight_count": len(player.unlocked_insights),
        "foundation_burst_triggered": player.foundation_burst_triggered,
        "breakthrough_insight_choices": max(0, player.breakthrough_count - player.breakthrough_insight_pending),
        **{f"insight_{name}": has_insight(player, name) for name in TRACKED_INSIGHTS},
        "theft_skill": player.theft_skill,
        "theft_attempts": player.theft_attempts,
        "theft_successes": player.theft_successes,
        "theft_failures": player.theft_failures,
        "theft_compensations": player.theft_compensations,
        "theft_refusals": player.theft_refusals,
        "theft_escape_count": player.theft_escape_count,
        "reputation": player.reputation,
        "enemy_count": player.enemy_count,
        "stolen_manual_fragments": player.stolen_manual_fragments,
        "stolen_cultivation_count": player.stolen_cultivation_count,
        "stolen_luck_count": player.stolen_luck_count,
        "stolen_opportunity_count": player.stolen_opportunity_count,
        "stolen_fate_count": player.stolen_fate_count,
        "stolen_lifespan_count": player.stolen_lifespan_count,
        "stolen_inheritance_count": player.stolen_inheritance_count,
        "theft_high_tier_attempts": player.theft_high_tier_attempts,
        "theft_high_tier_successes": player.theft_high_tier_successes,
        "theft_monthly_event_count": player.theft_monthly_event_count,
        "theft_exposure_gain": player.theft_exposure_gain,
        "theft_karma_gain": player.theft_karma_gain,
    }


def average(records: List[Dict[str, object]], key: str) -> float:
    return sum(float(record[key]) for record in records) / len(records)


def rate(records: List[Dict[str, object]], key: str) -> float:
    return sum(1 for record in records if record[key]) / len(records)


def summarize_route(route: Dict[str, object], runs: int) -> Dict[str, float | str | int]:
    records = [run_single_game(route, index) for index in range(1, runs + 1)]
    total_theft_attempts = sum(int(record["theft_attempts"]) for record in records)
    total_theft_successes = sum(int(record["theft_successes"]) for record in records)
    return {
        "name": str(route["name"]),
        "runs": runs,
        "avg_rank": average(records, "rank"),
        "top_ten_rate": rate(records, "top_ten"),
        "top_three_rate": rate(records, "top_three"),
        "first_rate": rate(records, "first"),
        "avg_total": average(records, "total"),
        "avg_realm": average(records, "realm_level"),
        "avg_progress": average(records, "cultivation_progress"),
        "avg_exposure": average(records, "exposure"),
        "avg_heart": average(records, "heart_demon"),
        "avg_demonic_qi": average(records, "demonic_qi"),
        "avg_karma": average(records, "karma"),
        "avg_stones": average(records, "spirit_stones"),
        "avg_herbs": average(records, "herbs"),
        "avg_aged_10": average(records, "aged_herbs_10"),
        "avg_aged_30": average(records, "aged_herbs_30"),
        "avg_intelligence": average(records, "intelligence"),
        "avg_talisman_bonus": average(records, "talisman_bonus"),
        "avg_risk_score": average(records, "risk_score"),
        "jade_bottle_rate": rate(records, "has_jade_bottle"),
        "soul_banner_rate": rate(records, "has_soul_banner"),
        "magic_flag_rate": rate(records, "magic_flag"),
        "jade_flag_rate": rate(records, "jade_flag"),
        "theft_negative_flag_rate": rate(records, "theft_negative_flag"),
        "high_risk_rate": rate(records, "high_risk"),
        "avg_heishui_spent": average(records, "heishui_spent"),
        "avg_heishui_purchase_count": average(records, "heishui_purchase_count"),
        "avg_heishui_intel_purchase_count": average(records, "heishui_intel_purchase_count"),
        "avg_heishui_black_market_purchase_count": average(records, "heishui_black_market_purchase_count"),
        "avg_heishui_blindbox_purchase_count": average(records, "heishui_blindbox_purchase_count"),
        "avg_tracking_marks": average(records, "tracking_marks"),
        "avg_heishui_risk_event_count": average(records, "heishui_risk_event_count"),
        "avg_heishui_blindbox_net": average(records, "heishui_blindbox_net"),
        "avg_spirit_field_harvest_count": average(records, "spirit_field_harvest_count"),
        "avg_furnace_level": average(records, "furnace_level"),
        "avg_equipment_count": average(records, "equipment_count"),
        "avg_equipment_score": average(records, "equipment_score"),
        "avg_foundation": average(records, "foundation"),
        "avg_breadth": average(records, "breadth"),
        "avg_mastery_total": average(records, "mastery_total"),
        "avg_unlocked_insight_count": average(records, "unlocked_insight_count"),
        "foundation_burst_rate": rate(records, "foundation_burst_triggered"),
        "avg_breakthrough_insight_choices": average(records, "breakthrough_insight_choices"),
        **{f"rate_{name}": rate(records, f"insight_{name}") for name in TRACKED_INSIGHTS},
        "avg_theft_skill": average(records, "theft_skill"),
        "avg_theft_attempts": average(records, "theft_attempts"),
        "theft_success_rate": total_theft_successes / total_theft_attempts if total_theft_attempts else 0.0,
        "avg_theft_compensations": average(records, "theft_compensations"),
        "avg_theft_refusals": average(records, "theft_refusals"),
        "avg_theft_escape_count": average(records, "theft_escape_count"),
        "avg_reputation": average(records, "reputation"),
        "avg_enemy_count": average(records, "enemy_count"),
        "avg_stolen_manual_fragments": average(records, "stolen_manual_fragments"),
        "avg_stolen_cultivation_count": average(records, "stolen_cultivation_count"),
        "avg_stolen_luck_count": average(records, "stolen_luck_count"),
        "avg_stolen_opportunity_count": average(records, "stolen_opportunity_count"),
        "avg_stolen_fate_count": average(records, "stolen_fate_count"),
        "avg_stolen_lifespan_count": average(records, "stolen_lifespan_count"),
        "avg_stolen_inheritance_count": average(records, "stolen_inheritance_count"),
        "avg_theft_high_tier_attempts": average(records, "theft_high_tier_attempts"),
        "avg_theft_high_tier_successes": average(records, "theft_high_tier_successes"),
        "avg_theft_monthly_event_count": average(records, "theft_monthly_event_count"),
        "avg_theft_exposure_gain": average(records, "theft_exposure_gain"),
        "avg_theft_karma_gain": average(records, "theft_karma_gain"),
    }


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_summary(summary: Dict[str, float | str | int]) -> None:
    print()
    print(f"流派：{summary['name']}")
    print(f"模拟局数：{summary['runs']}局")
    print(f"平均名次：{summary['avg_rank']:.1f}")
    print(f"前十率：{pct(float(summary['top_ten_rate']))}")
    print(f"前三率：{pct(float(summary['top_three_rate']))}")
    print(f"第一率：{pct(float(summary['first_rate']))}")
    print(f"平均总分：{summary['avg_total']:.1f}")
    print(f"平均境界：炼气{summary['avg_realm']:.1f}层")
    print(f"平均修炼进度：{summary['avg_progress']:.1f}")
    print(f"平均暴露度：{summary['avg_exposure']:.1f}")
    print(f"平均心魔值：{summary['avg_heart']:.1f}")
    print(f"平均魔气值：{summary['avg_demonic_qi']:.1f}")
    print(f"平均业力值：{summary['avg_karma']:.1f}")
    print(f"平均灵石：{summary['avg_stones']:.1f}")
    print(f"平均普通灵草：{summary['avg_herbs']:.1f}")
    print(f"平均十年份灵草：{summary['avg_aged_10']:.1f}")
    print(f"平均三十年份灵草：{summary['avg_aged_30']:.1f}")
    print(f"平均情报值：{summary['avg_intelligence']:.1f}")
    print(f"平均符箓加成：{summary['avg_talisman_bonus']:.1f}")
    print(f"平均风险：{summary['avg_risk_score']:.1f}")
    print(f"古玉瓶获得率：{pct(float(summary['jade_bottle_rate']))}")
    print(f"残破魂幡获得率：{pct(float(summary['soul_banner_rate']))}")
    print(f"魔影伏身结局标记率：{pct(float(summary['magic_flag_rate']))}")
    print(f"玉瓶生疑结局标记率：{pct(float(summary['jade_flag_rate']))}")
    print(f"盗术大比负面标记率：{pct(float(summary['theft_negative_flag_rate']))}")
    print(f"高风险局率：{pct(float(summary['high_risk_rate']))}")
    print(f"平均黑水坊市消费：{summary['avg_heishui_spent']:.1f}")
    print(f"平均黑水购买次数：{summary['avg_heishui_purchase_count']:.1f}")
    print(f"情报购买次数：{summary['avg_heishui_intel_purchase_count']:.1f}")
    print(f"黑市购买次数：{summary['avg_heishui_black_market_purchase_count']:.1f}")
    print(f"盲盒购买次数：{summary['avg_heishui_blindbox_purchase_count']:.1f}")
    print(f"追踪标记平均值：{summary['avg_tracking_marks']:.1f}")
    print(f"月末黑水风险事件触发次数：{summary['avg_heishui_risk_event_count']:.1f}")
    print(f"盲盒平均净收益：{summary['avg_heishui_blindbox_net']:.1f}")
    print(f"平均灵田收获次数：{summary['avg_spirit_field_harvest_count']:.1f}")
    print(f"平均炼丹炉等级：{summary['avg_furnace_level']:.1f}")
    print(f"平均装备数量：{summary['avg_equipment_count']:.1f}")
    print(f"平均装备评分：{summary['avg_equipment_score']:.1f}")
    print(f"平均根基：{summary['avg_foundation']:.1f}")
    print(f"平均博学度：{summary['avg_breadth']:.1f}")
    print(f"平均熟练度总和：{summary['avg_mastery_total']:.1f}")
    print(f"平均解锁融会状态数量：{summary['avg_unlocked_insight_count']:.1f}")
    print(f"静水深流触发率：{pct(float(summary['rate_静水深流']))}")
    print(f"法随心动触发率：{pct(float(summary['rate_法随心动']))}")
    print(f"药理通明触发率：{pct(float(summary['rate_药理通明']))}")
    print(f"山野老手触发率：{pct(float(summary['rate_山野老手']))}")
    print(f"族中耳目触发率：{pct(float(summary['rate_族中耳目']))}")
    print(f"妙手无痕触发率：{pct(float(summary['rate_妙手无痕']))}")
    print(f"百艺旁通触发率：{pct(float(summary['rate_百艺旁通']))}")
    print(f"万法互证触发率：{pct(float(summary['rate_万法互证']))}")
    print(f"厚积薄发触发率：{pct(float(summary['foundation_burst_rate']))}")
    print(f"平均突破感悟选择次数：{summary['avg_breakthrough_insight_choices']:.1f}")
    print(f"平均盗术等级：{summary['avg_theft_skill']:.1f}")
    print(f"平均偷窃次数：{summary['avg_theft_attempts']:.1f}")
    print(f"偷窃成功率：{pct(float(summary['theft_success_rate']))}")
    print(f"平均赔偿次数：{summary['avg_theft_compensations']:.1f}")
    print(f"平均拒赔次数：{summary['avg_theft_refusals']:.1f}")
    print(f"平均强行脱身次数：{summary['avg_theft_escape_count']:.1f}")
    print(f"平均旁门声望：{summary['avg_reputation']:.1f}")
    print(f"平均结仇数量：{summary['avg_enemy_count']:.1f}")
    print(f"偷功法/残页数量：{summary['avg_stolen_manual_fragments']:.1f}")
    print(f"偷修为次数：{summary['avg_stolen_cultivation_count']:.1f}")
    print(f"偷气运次数：{summary['avg_stolen_luck_count']:.1f}")
    print(f"偷机缘次数：{summary['avg_stolen_opportunity_count']:.1f}")
    print(f"偷因果次数：{summary['avg_stolen_fate_count']:.1f}")
    print(f"偷寿元次数：{summary['avg_stolen_lifespan_count']:.1f}")
    print(f"偷 NPC 传承次数：{summary['avg_stolen_inheritance_count']:.2f}")
    print(f"高阶盗术触发次数：{summary['avg_theft_high_tier_attempts']:.1f}")
    print(f"高阶盗术成功次数：{summary['avg_theft_high_tier_successes']:.1f}")
    print(f"月末盗术反噬次数：{summary['avg_theft_monthly_event_count']:.1f}")
    print(f"盗术导致平均暴露增量：{summary['avg_theft_exposure_gain']:.1f}")
    print(f"盗术导致平均业力增量：{summary['avg_theft_karma_gain']:.1f}")
    print(f"综合评价：{route_assessment(summary)}")


def route_assessment(summary: Dict[str, float | str | int]) -> str:
    name = str(summary["name"])
    top_ten = float(summary["top_ten_rate"])
    top_three = float(summary["top_three_rate"])
    exposure = float(summary["avg_exposure"])
    heart = float(summary["avg_heart"])
    karma = float(summary["avg_karma"])
    stones = float(summary["avg_stones"])
    avg_rank = float(summary["avg_rank"])
    high_risk = float(summary["high_risk_rate"])
    risk_events = float(summary.get("avg_heishui_risk_event_count", 0))
    blindbox_net = float(summary.get("avg_heishui_blindbox_net", 0))
    intel_count = float(summary.get("avg_heishui_intel_purchase_count", 0))

    if name == "厚积薄发流":
        burst_rate = float(summary.get("foundation_burst_rate", 0))
        wanfa_rate = float(summary.get("rate_万法互证", 0))
        if top_ten < 0.35:
            return "慢热路线过弱，根基和多门熟练度未能转化为足够大比竞争力。"
        if top_ten > 0.85:
            return "综合路线过强，需要压低融会或厚积薄发收益。"
        if top_three > 0.15:
            return "后期爆发过强，前三率偏高。"
        if wanfa_rate > 0.50:
            return "万法互证触发偏多，博学门槛可能过低。"
        if burst_rate < 0.10:
            return "厚积薄发触发偏少，条件可能过苛刻。"
        if burst_rate > 0.70:
            return "厚积薄发触发过于常见，综合路线缺少稀缺性。"
        return "根基、博学和厚积薄发处于观察区间。"

    if name == "盗术投机流":
        high_tier = float(summary.get("avg_theft_high_tier_successes", 0))
        high_tier_attempts = float(summary.get("avg_theft_high_tier_attempts", 0))
        failure_resolution = (
            float(summary.get("avg_theft_compensations", 0))
            + float(summary.get("avg_theft_refusals", 0))
            + float(summary.get("avg_theft_escape_count", 0))
        )
        if top_ten > 0.90:
            return "盗术投机流过强，需要压低盗术收益或提高风险。"
        if top_three > 0.20:
            return "高阶盗术收益过高，前三率偏危险。"
        if float(summary.get("avg_stolen_cultivation_count", 0)) > 2.0 and high_risk < 0.25:
            return "偷修为次数较多且平均风险偏低，代价不足。"
        if high_tier > 0.9 or high_tier_attempts > 2.2:
            return "偷气运/机缘/因果/寿元/传承触发偏频繁。"
        if float(summary.get("avg_theft_attempts", 0)) > 2 and failure_resolution < 0.15:
            return "失败后的赔偿/拒赔/强逃覆盖不足。"
        if top_ten < 0.30:
            return "盗术投机流偏弱，爆点不足。"
        return "盗术收益、失败处理和反噬处于观察区间。"

    if name == "随心游玩流":
        if top_ten < 0.25:
            return "普通玩家体验可能过挫败。"
        if top_ten > 0.85:
            return "随意游玩也过强，整体难度偏低。"
        if top_three > 0.20:
            return "随机游玩上限偏高，需要降低通用收益。"
        if risk_events >= 0.80 and avg_rank > 18:
            return "黑水坊市对普通玩家惩罚过重。"
        if risk_events < 0.05:
            return "随机玩家与黑水内容接触不足。"
        return "普通随机游玩表现处于可观察区间。"

    if top_ten < 0.30:
        return "偏弱，需要确认是否仍能作为可玩路线。"
    if exposure > 70:
        return "收益伴随高暴露，属于高压路线。"
    if name == "魔道炼魂流":
        if top_three > 0.50 and high_risk < 0.30:
            return "冲榜能力强但坏结局和风险仍偏低。"
        if high_risk >= 0.40 or heart >= 35 or karma >= 30:
            return "高收益伴随明显魔道代价。"
    if name == "坊市符箓流" and stones > 18 and avg_rank <= 5:
        return "名次高且资源宽裕，坊市价格仍可能偏低。"
    if name == "纯打坐流":
        if top_three > 0.50:
            return "基础修炼冲榜能力仍偏强。"
        return "低风险且较稳定，适合作为新手保底。"
    if name == "黑水投机流":
        if top_ten > 0.90:
            return "黑水坊市收益过稳，需要继续加风险或压收益。"
        if top_three > 0.30 and risk_events < 1:
            return "黑水冲榜能力强但风险事件不足。"
        if blindbox_net > 0 and high_risk < 0.20:
            return "盲盒期望偏高且风险偏低。"
        if intel_count >= 4 and avg_rank <= 6:
            return "情报购买较多且名次靠前，需观察情报收益。"
        return "投机收益和风险处于观察区间。"
    if top_ten > 0.90 or top_three > 0.50:
        return "整体偏强，后续可继续提高赛事压力。"
    return "表现处于可观察区间。"


def evaluate(summaries: List[Dict[str, float | str | int]]) -> List[str]:
    notes: List[str] = []
    if all(float(summary["top_ten_rate"]) > 0.90 for summary in summaries):
        notes.append("所有路线前十率都高于90%，整体赛事难度偏低或成长速度偏快。")
    for summary in summaries:
        name = str(summary["name"])
        top_ten = float(summary["top_ten_rate"])
        top_three = float(summary["top_three_rate"])
        exposure = float(summary["avg_exposure"])
        heart = float(summary["avg_heart"])
        karma = float(summary["avg_karma"])
        stones = float(summary["avg_stones"])
        avg_rank = float(summary["avg_rank"])
        high_risk = float(summary["high_risk_rate"])
        risk_events = float(summary.get("avg_heishui_risk_event_count", 0))
        blindbox_net = float(summary.get("avg_heishui_blindbox_net", 0))
        intel_count = float(summary.get("avg_heishui_intel_purchase_count", 0))
        theft_attempts = float(summary.get("avg_theft_attempts", 0))
        theft_resolutions = (
            float(summary.get("avg_theft_compensations", 0))
            + float(summary.get("avg_theft_refusals", 0))
            + float(summary.get("avg_theft_escape_count", 0))
        )
        theft_high_tier = (
            float(summary.get("avg_theft_high_tier_successes", 0))
        )
        theft_high_tier_attempts = float(summary.get("avg_theft_high_tier_attempts", 0))
        burst_rate = float(summary.get("foundation_burst_rate", 0))
        wanfa_rate = float(summary.get("rate_万法互证", 0))
        avg_breadth = float(summary.get("avg_breadth", 0))

        if name != "随心游玩流" and top_ten < 0.30:
            notes.append(f"{name}：前十率低于30%，该路线可能过弱。")
        if name != "随心游玩流" and top_ten > 0.90:
            notes.append(f"{name}：前十率高于90%，该路线可能过强。")
        if name != "随心游玩流" and top_three > 0.50:
            notes.append(f"{name}：前三率高于50%，该路线可能过强。")
        if exposure > 70:
            notes.append(f"{name}：平均暴露度超过70，该路线暴露风险过高。")
        if name == "魔道炼魂流" and top_ten > 0.60 and heart < 25 and karma < 25:
            notes.append("魔道炼魂流：前十率较高但心魔/业力偏低，魔道代价不足。")
        if name == "魔道炼魂流" and top_three > 0.50 and high_risk < 0.30:
            notes.append("魔道炼魂流：前三率高但坏结局/风险不高，魔道代价不足。")
        if name == "坊市符箓流" and stones > 18 and avg_rank <= 5:
            notes.append("坊市符箓流：资源剩余过多且名次高，坊市价格偏低。")
        if name == "纯打坐流" and top_ten < 0.30:
            notes.append("纯打坐流：前十率过低，新手保底不足。")
        if name == "纯打坐流" and top_three > 0.50:
            notes.append("纯打坐流：前三率过高，基础修炼收益过强。")
        if name == "纯打坐流" and top_ten > 0.90 and top_three > 0.50:
            notes.append("纯打坐流：前十率和前三率都偏高，策略性不足。")
        if name == "黑水投机流" and top_ten > 0.90:
            notes.append("黑水投机流：前十率超过90%，黑水坊市收益过稳。")
        if name == "黑水投机流" and top_three > 0.30 and risk_events < 1:
            notes.append("黑水投机流：前三率超过30%且风险事件很少，黑水风险不足。")
        if name == "黑水投机流" and blindbox_net > 0 and high_risk < 0.20:
            notes.append("黑水投机流：盲盒平均收益为正且风险很低，盲盒期望值过高。")
        if name == "黑水投机流" and intel_count >= 4 and avg_rank <= 6:
            notes.append("黑水投机流：情报购买次数高但名次明显靠前，情报收益过稳。")
        if name == "盗术投机流":
            if top_ten > 0.90:
                notes.append("盗术投机流：前十率超过90%，盗术过强。")
            if top_three > 0.20:
                notes.append("盗术投机流：前三率超过20%，高阶盗术收益过高。")
            if float(summary.get("avg_stolen_cultivation_count", 0)) > 2.0 and high_risk < 0.25:
                notes.append("盗术投机流：偷修为次数过多且平均风险低，偷修为代价不足。")
            if theft_high_tier > 0.9 or theft_high_tier_attempts > 2.2:
                notes.append("盗术投机流：偷气运/机缘/因果/寿元/传承频率过高。")
            if theft_attempts > 2 and theft_resolutions < 0.15:
                notes.append("盗术投机流：失败后赔偿/拒赔/强逃几乎不发生，失败事件覆盖不足。")
        if name == "厚积薄发流":
            if top_ten < 0.35:
                notes.append("厚积薄发流：前十率低于35%，慢热路线过弱。")
            if top_ten > 0.85:
                notes.append("厚积薄发流：前十率高于85%，综合路线过强。")
            if top_three > 0.15:
                notes.append("厚积薄发流：前三率高于15%，后期爆发过强。")
            if wanfa_rate > 0.50:
                notes.append("厚积薄发流：万法互证触发率超过50%，博学门槛过低。")
            if burst_rate < 0.10:
                notes.append("厚积薄发流：厚积薄发触发率低于10%，条件过苛刻。")
            if burst_rate > 0.70:
                notes.append("厚积薄发流：厚积薄发触发率高于70%，触发过于常见。")
        if name == "随心游玩流":
            if top_ten < 0.25:
                notes.append("随心游玩流：普通玩家体验可能过挫败。")
            if top_ten > 0.85:
                notes.append("随心游玩流：随意游玩也过强，整体难度偏低。")
            if top_three > 0.20:
                notes.append("随心游玩流：随机游玩上限偏高，需要降低通用收益。")
            if risk_events >= 0.80 and avg_rank > 18:
                notes.append("随心游玩流：黑水坊市对普通玩家惩罚过重。")
            if risk_events < 0.05:
                notes.append("随心游玩流：随机玩家与黑水内容接触不足。")

    if all(float(summary.get("avg_breadth", 0)) >= 6 for summary in summaries) and all(
        float(summary["top_ten_rate"]) > 0.75 for summary in summaries
    ):
        notes.append("平均博学度普遍偏高且所有路线都偏强，博学加成可能过强。")

    if not notes:
        notes.append("未发现明显红线。")
    return notes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="自动模拟第一章不同流派的数值表现。")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="每个流派模拟局数，默认200。")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="随机种子，默认20260527。")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    runs = max(1, int(args.runs))
    random.seed(int(args.seed))

    print(f"=== {VERSION} 自动模拟结果 ===")
    print(f"随机种子：{args.seed}")
    print(f"每个流派模拟：{runs}局")

    summaries = [summarize_route(route, runs) for route in ROUTES]
    for summary in summaries:
        print_summary(summary)

    print()
    print("自动评价：")
    for note in evaluate(summaries):
        print(f"- {note}")


if __name__ == "__main__":
    main()
