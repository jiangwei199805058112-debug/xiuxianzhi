"""青岭沈家家族大比结算。"""

from __future__ import annotations

from typing import Dict, List

from player import Player


def _rank_from_score(score: int) -> int:
    if score >= 190:
        return 1
    if score >= 170:
        return 3
    if score >= 150:
        return 6
    if score >= 125:
        return 10
    if score >= 105:
        return 16
    if score >= 85:
        return 24
    return 32


def run_tournament(player: Player) -> Dict[str, object]:
    cultivation_score = (
        player.cultivation * 2
        + player.comprehension
        + player.root_growth * 5
        + min(player.pills, 5) * 2
        - player.heart_demon // 5
    )
    combat_score = (
        player.combat_exp * 2
        + player.physique
        + player.cultivation // 2
        + min(player.souls_refined, 4) * 3
        - player.demonic_qi // 4
        - player.karma // 8
    )
    conduct_score = (
        player.righteous_reputation * 2
        + player.contribution
        + int(player.average_affection() // 2)
        + max(0, 30 - player.exposure // 2)
        - player.heart_demon // 3
        - player.karma // 4
        - player.demonic_qi // 5
    )

    scores = {
        "第一关：测灵验阶": max(0, cultivation_score),
        "第二关：演武斗法": max(0, combat_score),
        "第三关：问心家评": max(0, conduct_score),
    }
    total = sum(scores.values())
    rank = _rank_from_score(total)
    top_ten = rank <= 10

    flags: List[str] = []
    if player.exposure >= 75:
        flags.append("玉瓶生疑")
    if player.demonic_qi >= 60 or player.karma >= 60:
        flags.append("魔影伏身")
    if player.heart_demon >= 75:
        flags.append("心魔暗结")
    if player.average_affection() >= 45:
        flags.append("旁支有人")

    if top_ten and "魔影伏身" not in flags:
        ending = "前十入册"
        summary = "你以旁支身份挤入青岭沈家大比前十，得以进入族中更深处的修行名单。"
    elif top_ten:
        ending = "前十蒙尘"
        summary = "你确实打入前十，却因魔气与业力过重，被族老暗中记下。"
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
    }


def format_tournament_result(result: Dict[str, object]) -> str:
    lines = ["\n===== 青岭沈家家族大比 ====="]
    scores = result["scores"]
    if isinstance(scores, dict):
        for name, score in scores.items():
            lines.append(f"{name}：{score}")
    lines.append(f"总分：{result['total']}")
    lines.append(f"名次：第 {result['rank']} 名")
    lines.append(f"目标：{'达成，进入前十' if result['top_ten'] else '未达成，未入前十'}")
    flags = result["flags"]
    if flags:
        lines.append("结算标记：" + "、".join(str(flag) for flag in flags))
    else:
        lines.append("结算标记：无")
    lines.append(f"结局：{result['ending']}")
    lines.append(str(result["summary"]))
    return "\n".join(lines)
