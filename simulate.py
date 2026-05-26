"""第一章数值平衡自动模拟工具。"""

from __future__ import annotations

import argparse
import builtins
from contextlib import redirect_stdout
import io
import random
from typing import Dict, Iterable, List, Tuple

from data import TOTAL_ACTIONS
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
    def __init__(self, route_name: str, player: Player) -> None:
        self.route_name = route_name
        self.player = player

    def __call__(self, prompt: str = "") -> str:
        if "古玉瓶用量" in prompt:
            return self.choose_jade_bottle()
        if "请选择商品" in prompt:
            return self.choose_market_good()
        if "请选择出售项" in prompt:
            return self.choose_herb_sale()
        if "请选择对象" in prompt:
            return self.choose_npc()
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
        if self.route_name == "古玉瓶炼丹流":
            if self.player.aged_herbs_30 > 0 or self.player.aged_herbs_10 > 0:
                return "B"
            return "A" if self.choose_market_good() != "0" else "C"
        if self.route_name in {"坊市符箓流", "均衡流"}:
            return "A" if self.choose_market_good() != "0" else "C"
        return "C"

    def choose_market_good(self) -> str:
        stones = self.player.spirit_stones
        if self.route_name == "古玉瓶炼丹流":
            if self.player.heart_demon >= 10 and stones >= 15:
                return "6"
            if stones >= 12:
                return "4"
            if self.player.heart_demon >= 5 and stones >= 15:
                return "6"
            return "0"
        if self.route_name == "坊市符箓流":
            if self.player.talisman_guard < 2 and stones >= 20:
                return "7"
            if self.player.talisman_fire < 2 and stones >= 18:
                return "8"
            if stones >= 10:
                return "11"
            return "0"
        if self.route_name == "均衡流":
            if self.player.intelligence < 12 and stones >= 10:
                return "11"
            if stones >= 12:
                return "4"
            return "0"
        return "0"

    def choose_herb_sale(self) -> str:
        if self.player.aged_herbs_30 > 0:
            return "3"
        if self.player.aged_herbs_10 > 0:
            return "2"
        if self.player.herbs > 6:
            return "1"
        return "0"

    def choose_npc(self) -> str:
        if self.player.npc_affection.get("沈若兰", 0) < 35:
            return "1"
        if self.player.npc_affection.get("沈霜", 0) < 25:
            return "5"
        return "3"


def choose_route_action(route: Dict[str, object], player: Player) -> str:
    action = weighted_choice(route["weights"])  # type: ignore[arg-type]
    if action == "10" and not player.has_soul_banner:
        return "3" if random.random() < 0.65 else "1"
    return action


def run_single_game(route: Dict[str, object], index: int) -> Dict[str, object]:
    route_name = str(route["name"])
    player = create_player(f"{route_name}{index}")
    while not player.finished:
        action = choose_route_action(route, player)
        auto_input = AutoInput(route_name, player)
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
        "has_jade_bottle": player.has_jade_bottle,
        "has_soul_banner": player.has_soul_banner,
        "magic_flag": "魔影伏身" in result["flags"],
        "jade_flag": "玉瓶生疑" in result["flags"],
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
        "jade_bottle_rate": rate(records, "has_jade_bottle"),
        "soul_banner_rate": rate(records, "has_soul_banner"),
        "magic_flag_rate": rate(records, "magic_flag"),
        "jade_flag_rate": rate(records, "jade_flag"),
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
    print(f"古玉瓶获得率：{pct(float(summary['jade_bottle_rate']))}")
    print(f"残破魂幡获得率：{pct(float(summary['soul_banner_rate']))}")
    print(f"魔影伏身结局标记率：{pct(float(summary['magic_flag_rate']))}")
    print(f"玉瓶生疑结局标记率：{pct(float(summary['jade_flag_rate']))}")


def evaluate(summaries: List[Dict[str, float | str | int]]) -> List[str]:
    notes: List[str] = []
    for summary in summaries:
        name = str(summary["name"])
        top_ten = float(summary["top_ten_rate"])
        top_three = float(summary["top_three_rate"])
        exposure = float(summary["avg_exposure"])
        heart = float(summary["avg_heart"])
        karma = float(summary["avg_karma"])

        if top_ten < 0.30:
            notes.append(f"{name}：前十率低于30%，该路线可能过弱。")
        if top_ten > 0.90:
            notes.append(f"{name}：前十率高于90%，该路线可能过强。")
        if top_three > 0.50:
            notes.append(f"{name}：前三率高于50%，该路线可能过强。")
        if exposure > 70:
            notes.append(f"{name}：平均暴露度超过70，该路线暴露风险过高。")
        if name == "魔道炼魂流" and top_ten > 0.60 and heart < 25 and karma < 25:
            notes.append("魔道炼魂流：前十率较高但心魔/业力偏低，魔道代价不足。")
        if name == "纯打坐流" and top_ten < 0.30:
            notes.append("纯打坐流：前十率过低，新手保底不足。")
        if name == "纯打坐流" and top_ten > 0.90 and top_three > 0.50:
            notes.append("纯打坐流：前十率和前三率都偏高，策略性不足。")

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

    print("=== v0.1.3 自动模拟结果 ===")
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
