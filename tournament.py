"""青岭沈家家族大比结算。"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

from player import Player


NPC_SCORE_RANGES: List[Tuple[str, int, int]] = [
    ("沈云庭", 82, 88),
    ("沈若兰", 76, 82),
    ("沈子岳", 68, 76),
    ("沈怀安", 65, 73),
    ("沈霜", 62, 70),
    ("普通直系A", 60, 68),
    ("普通旁支A", 56, 64),
    ("法术偏科族人", 52, 62),
    ("药园弟子", 50, 60),
    ("符箓小户", 48, 58),
    ("低调黑马", 58, 75),
    ("弱势族人", 35, 50),
]


def _cap(score: int, maximum: int) -> int:
    return max(0, min(score, maximum))


def _build_leaderboard(player_name: str, player_score: int) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = [
        {"name": player_name, "score": player_score, "player": True}
    ]
    for name, low, high in NPC_SCORE_RANGES:
        entries.append({"name": name, "score": random.randint(low, high), "player": False})
    entries.sort(key=lambda item: (-int(item["score"]), 0 if item["player"] else 1, str(item["name"])))
    return entries


def _talisman_combat_bonus(player: Player) -> int:
    guard_bonus = min(player.talisman_guard, 2)
    fire_bonus = min(player.talisman_fire, 2)
    has_shen_yunting = any(name == "沈云庭" for name, _, _ in NPC_SCORE_RANGES)
    avoid_fire_bonus = min(player.talisman_avoid_fire, 1) if has_shen_yunting else 0
    break_armor_bonus = min(player.talisman_break_armor, 1)
    return min(5, guard_bonus + fire_bonus + avoid_fire_bonus + break_armor_bonus)


def run_tournament(player: Player) -> Dict[str, object]:
    mind_score = _cap(
        player.realm_level * 3
        + player.cultivation_progress // 10
        + player.root_growth * 2
        + player.dao_heart
        + player.divine_sense
        + player.righteous_reputation // 5
        - player.heart_demon // 5
        - player.demonic_qi // 8
        - player.karma // 8,
        25,
    )
    trial_score = _cap(
        player.physique
        + player.speed
        + player.luck * 2
        + player.intelligence * 2
        + player.herbs // 2
        + player.aged_herbs_10 * 2
        + player.aged_herbs_30 * 4
        + player.contribution // 3
        - player.exposure // 6,
        35,
    )
    talisman_bonus = _talisman_combat_bonus(player)
    combat_score = _cap(
        player.attack
        + player.defense
        + player.speed
        + player.mp // 4
        + player.combat_exp * 2
        + player.intelligence
        + min(player.souls_refined, 4) * 2
        + talisman_bonus
        - player.heart_demon // 8
        - player.demonic_qi // 5
        - player.karma // 8,
        40,
    )

    scores = {
        "测灵问心": mind_score,
        "百药山试炼": trial_score,
        "斗法台": combat_score,
    }
    total = sum(scores.values())
    leaderboard = _build_leaderboard(player.name, total)
    rank = next(index + 1 for index, entry in enumerate(leaderboard) if entry["player"])
    top_ten = rank <= 10

    flags: List[str] = []
    if player.has_jade_bottle and player.exposure >= 75:
        flags.append("玉瓶生疑")
    if player.has_soul_banner and (player.demonic_qi >= 60 or player.karma >= 60):
        flags.append("魔影伏身")
    if player.heart_demon >= 75:
        flags.append("心魔暗结")
    if player.average_affection() >= 35:
        flags.append("旁支有人")
    if player.intelligence >= 20:
        flags.append("情报先手")

    if top_ten and "魔影伏身" not in flags:
        ending = "前十入册"
        summary = "你以旁支身份挤入青岭沈家大比前十，第一章目标达成。"
    elif top_ten:
        ending = "前十蒙尘"
        summary = "你确实打入前十，却因残破魂幡带来的魔气与业力，被族老暗中记下。"
    elif "玉瓶生疑" in flags:
        ending = "旁支受查"
        summary = "你未入前十，古玉瓶的异常收益又露出痕迹，接下来只能更加谨慎。"
    else:
        ending = "旁支落榜"
        summary = "你没能进入前十，只保住了旁支子弟的普通名册。"

    player.ending_flags = flags
    player.clamp()
    return {
        "scores": scores,
        "total": total,
        "rank": rank,
        "top_ten": top_ten,
        "flags": flags,
        "ending": ending,
        "summary": summary,
        "leaderboard": leaderboard,
        "talisman_bonus": talisman_bonus,
    }


def format_tournament_result(result: Dict[str, object]) -> str:
    lines = ["\n===== 青岭沈家家族大比 ====="]
    lines.append("评分：100分制")
    scores = result["scores"]
    if isinstance(scores, dict):
        lines.append(f"测灵问心：{scores.get('测灵问心', 0)}/25")
        lines.append(f"百药山试炼：{scores.get('百药山试炼', 0)}/35")
        lines.append(f"斗法台：{scores.get('斗法台', 0)}/40")
    lines.append(f"符箓斗法加成：+{result.get('talisman_bonus', 0)}")
    lines.append(f"总分：{result['total']}/100")
    lines.append(f"名次：第 {result['rank']} 名")
    lines.append(f"目标：{'达成，进入前十' if result['top_ten'] else '未达成，未入前十'}")

    leaderboard = result.get("leaderboard", [])
    if isinstance(leaderboard, list):
        lines.append("排名表：")
        for index, entry in enumerate(leaderboard, start=1):
            marker = "（你）" if isinstance(entry, dict) and entry.get("player") else ""
            if isinstance(entry, dict):
                lines.append(f"{index}. {entry.get('name')}{marker}：{entry.get('score')}分")

    flags = result["flags"]
    if flags:
        lines.append("结算标记：" + "、".join(str(flag) for flag in flags))
    else:
        lines.append("结算标记：无")
    lines.append(f"结局：{result['ending']}")
    lines.append(str(result["summary"]))
    return "\n".join(lines)
