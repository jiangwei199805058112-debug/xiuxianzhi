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
    guard_bonus = 1 if player.talisman_guard > 0 else 0
    fire_bonus = 1 if player.talisman_fire > 0 else 0
    has_shen_yunting = any(name == "沈云庭" for name, _, _ in NPC_SCORE_RANGES)
    avoid_fire_bonus = min(player.talisman_avoid_fire, 1) if has_shen_yunting else 0
    break_armor_bonus = min(player.talisman_break_armor, 1)
    return min(3, guard_bonus + fire_bonus + avoid_fire_bonus + break_armor_bonus)


def _intel_bonus(player: Player, section: str, cap_value: int = 2) -> int:
    bonus = int(player.heishui_tournament_bonuses.get(section, 0))
    return max(-cap_value, min(cap_value, bonus))


def run_tournament(player: Player) -> Dict[str, object]:
    mind_intel_bonus = _intel_bonus(player, "mind")
    trial_intel_bonus = _intel_bonus(player, "trial")
    combat_intel_bonus = _intel_bonus(player, "combat")
    mind_score = _cap(
        player.realm_level * 2
        + player.cultivation_progress // 15
        + player.root_growth
        + player.dao_heart // 2
        + player.divine_sense
        + min(player.pills, 5)
        + player.righteous_reputation // 8
        - player.heart_demon // 3
        - player.demonic_qi // 4
        - player.karma // 4
        - max(0, player.exposure - 50) // 8
        + mind_intel_bonus,
        25,
    )
    trial_score = _cap(
        player.physique
        + player.speed // 2
        + player.luck
        + player.intelligence // 4
        + min(player.herbs, 12) // 4
        + player.aged_herbs_10
        + player.aged_herbs_30 * 2
        + player.contribution // 4
        + min(player.spirit_stones // 10, 3)
        - player.exposure // 4
        - player.heart_demon // 8
        - player.karma // 8
        + trial_intel_bonus,
        35,
    )
    talisman_bonus = _talisman_combat_bonus(player)
    combat_score = _cap(
        player.attack // 3
        + player.defense // 2
        + player.speed // 2
        + player.mp // 12
        + player.combat_exp // 3
        + player.intelligence // 6
        + min(player.pills, 5)
        + min(player.souls_refined, 4)
        + talisman_bonus
        - player.heart_demon // 5
        - player.demonic_qi // 3
        - player.karma // 3
        - max(0, player.exposure - 35) // 6
        + combat_intel_bonus,
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
    if player.has_soul_banner and (player.demonic_qi >= 45 or player.karma >= 35 or player.heart_demon >= 55):
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
        "heishui_intel_bonus": mind_intel_bonus + trial_intel_bonus + combat_intel_bonus,
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
    if result.get("heishui_intel_bonus", 0):
        lines.append(f"黑水情报修正：{int(result.get('heishui_intel_bonus', 0)):+d}")
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
