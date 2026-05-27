"""第一章数值平衡自动模拟工具。"""

from __future__ import annotations

import argparse
import builtins
from contextlib import redirect_stdout
import io
import random
from typing import Dict, Iterable, List, Tuple

from data import MARKET_GOODS, NPCS, TOTAL_ACTIONS, VERSION
from heishui_market import ensure_market_state, load_config, shop_unlock_reason
from player import Player, create_player
from systems import monthly_event, perform_action
from tournament import run_tournament

DEFAULT_RUNS = 200
DEFAULT_SEED = 20260527

ROUTES: List[Dict[str, object]] = [
    {
        "name": "纯打坐流",
        "weights": [("1", 70), ("8", 15), ("9", 10), ("12", 5)],
    },
    {
        "name": "古玉瓶炼丹流",
        "weights": [("2", 25), ("6", 20), ("5", 15), ("1", 25), ("9", 10), ("12", 5)],
    },
    {
        "name": "坊市符箓流",
        "weights": [("3", 20), ("5", 30), ("1", 20), ("8", 15), ("9", 10), ("12", 5)],
    },
    {
        "name": "魔道炼魂流",
        "weights": [("3", 25), ("10", 25), ("1", 20), ("8", 15), ("4", 10), ("12", 5)],
    },
    {
        "name": "均衡流",
        "weights": [("1", 25), ("2", 15), ("3", 15), ("5", 15), ("8", 10), ("9", 10), ("7", 5), ("12", 5)],
    },
    {
        "name": "黑水投机流",
        "weights": [("5", 42), ("3", 24), ("4", 14), ("1", 10), ("9", 5), ("12", 5)],
    },
    {
        "name": "随心游玩流",
        "weights": [
            ("1", 5),
            ("3", 9),
            ("4", 8),
            ("8", 3),
            ("6", 3),
            ("5_normal", 8),
            ("5_heishui", 36),
            ("7", 8),
            ("12", 20),
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
        if self.route_name in {"坊市符箓流", "均衡流"}:
            return "A" if self.choose_market_good() != "0" else "C"
        return "C"

    def choose_casual_market_mode(self) -> str:
        if self.action_token == "5_heishui":
            if self.is_casual_high_risk() and random.random() < 0.60:
                return "E"
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
        return "E"

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
            ("shop_tanwei", 45),
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
            shop_weights.append(("shop_heishi", 4))

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
        if not self.is_casual_high_risk() and self.player.spirit_stones >= 20:
            tanwei_affordable = any(shop_id == "shop_tanwei" for shop_id, _ in candidates)
            tanwei_chance = 0.90 if self.player.heishui_blindbox_purchase_count == 0 else 0.60
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
            "黑市暗号线索": 26,
            "听曲静心": 16,
            "打听小道消息": 22,
            "染尘旧储物袋": 50,
            "赌石": 2,
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
                weight = max(weight, 1)
            if self.target_shop_id == "shop_heishi":
                weight = 1 if not self.is_casual_high_risk() else 0
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
        )


def choose_route_action(route: Dict[str, object], player: Player) -> str:
    if str(route["name"]) == "随心游玩流":
        high_risk = (
            player.exposure >= 55
            or player.heart_demon >= 35
            or player.demonic_qi >= 25
            or player.karma >= 25
            or player.tracking_marks > 0
            or player.heishui_risk_event_count > 0
        )
        if high_risk and random.random() < 0.35:
            return "12"
        if player.hp < player.max_hp * 0.35 and random.random() < 0.25:
            return "12"

    action = weighted_choice(route["weights"])  # type: ignore[arg-type]
    if str(route["name"]) == "随心游玩流" and high_risk and action == "5_heishui" and random.random() < 0.65:
        return "12" if random.random() < 0.60 else "5_normal"
    if action == "10" and not player.has_soul_banner:
        return "3" if random.random() < 0.65 else "1"
    return action


def action_choice_from_token(action_token: str) -> str:
    if action_token in {"5_normal", "5_heishui"}:
        return "5"
    return action_token


def risk_score(player: Player) -> int:
    return (
        player.exposure
        + player.heart_demon
        + player.demonic_qi
        + player.karma
        + player.tracking_marks * 8
        + player.heishui_risk_event_count * 10
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
                if player.total_actions == before:
                    player.advance_action()
                if player.total_actions % 3 == 0 and not player.finished:
                    monthly_event(player)
        finally:
            builtins.input = old_input

    result = run_tournament(player)
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
        "magic_flag": "魔影伏身" in result["flags"],
        "jade_flag": "玉瓶生疑" in result["flags"],
        "high_risk": (
            player.exposure >= 70
            or player.heart_demon >= 60
            or player.demonic_qi >= 45
            or player.karma >= 35
            or player.tracking_marks >= 2
            or player.heishui_risk_event_count >= 2
            or "魔影伏身" in result["flags"]
            or "玉瓶生疑" in result["flags"]
        ),
        "heishui_spent": player.heishui_market_spent,
        "heishui_purchase_count": player.heishui_purchase_count,
        "heishui_intel_purchase_count": player.heishui_intel_purchase_count,
        "heishui_black_market_purchase_count": player.heishui_black_market_purchase_count,
        "heishui_blindbox_purchase_count": player.heishui_blindbox_purchase_count,
        "tracking_marks": player.tracking_marks,
        "heishui_risk_event_count": player.heishui_risk_event_count,
        "heishui_blindbox_net": player.heishui_blindbox_net,
    }


def average(records: List[Dict[str, object]], key: str) -> float:
    return sum(float(record[key]) for record in records) / len(records)


def rate(records: List[Dict[str, object]], key: str) -> float:
    return sum(1 for record in records if record[key]) / len(records)


def summarize_route(route: Dict[str, object], runs: int) -> Dict[str, float | str | int]:
    records = [run_single_game(route, index) for index in range(1, runs + 1)]
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
        "high_risk_rate": rate(records, "high_risk"),
        "avg_heishui_spent": average(records, "heishui_spent"),
        "avg_heishui_purchase_count": average(records, "heishui_purchase_count"),
        "avg_heishui_intel_purchase_count": average(records, "heishui_intel_purchase_count"),
        "avg_heishui_black_market_purchase_count": average(records, "heishui_black_market_purchase_count"),
        "avg_heishui_blindbox_purchase_count": average(records, "heishui_blindbox_purchase_count"),
        "avg_tracking_marks": average(records, "tracking_marks"),
        "avg_heishui_risk_event_count": average(records, "heishui_risk_event_count"),
        "avg_heishui_blindbox_net": average(records, "heishui_blindbox_net"),
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
    print(f"高风险局率：{pct(float(summary['high_risk_rate']))}")
    print(f"平均黑水坊市消费：{summary['avg_heishui_spent']:.1f}")
    print(f"平均黑水购买次数：{summary['avg_heishui_purchase_count']:.1f}")
    print(f"情报购买次数：{summary['avg_heishui_intel_purchase_count']:.1f}")
    print(f"黑市购买次数：{summary['avg_heishui_black_market_purchase_count']:.1f}")
    print(f"盲盒购买次数：{summary['avg_heishui_blindbox_purchase_count']:.1f}")
    print(f"追踪标记平均值：{summary['avg_tracking_marks']:.1f}")
    print(f"月末黑水风险事件触发次数：{summary['avg_heishui_risk_event_count']:.1f}")
    print(f"盲盒平均净收益：{summary['avg_heishui_blindbox_net']:.1f}")
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
