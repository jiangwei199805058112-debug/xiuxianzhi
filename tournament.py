"""青岭沈家家族大比结算。"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

from cultivation_assets import equipment_bonus, equipment_score, furnace_level, grant_equipment, material_total
from chapter1_events import format_chapter1_event_log, process_chapter1_monthly_events
from growth_system import calculate_breadth, foundation_burst_bonus, growth_tournament_adjustments
from player import Player
from playtest_logger import format_playtest_report, summarize_month
from theft_system import theft_tournament_adjustments


NPC_SCORE_RANGES: List[Tuple[str, int, int]] = [
    ("沈云庭", 82, 88),
    ("沈若兰", 76, 82),
    ("沈子岳", 68, 76),
    ("沈怀安", 65, 73),
    ("沈霜", 62, 70),
    ("普通直系A", 61, 69),
    ("普通旁支A", 56, 64),
    ("法术偏科族人", 52, 62),
    ("药园弟子", 50, 60),
    ("符箓小户", 49, 59),
    ("低调黑马", 59, 76),
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
    guard_bonus = 1 if player.talisman_guard > 0 and player.defense < 14 else 0
    fire_bonus = 1 if player.talisman_fire > 0 and player.attack < 16 else 0
    has_shen_yunting = any(name == "沈云庭" for name, _, _ in NPC_SCORE_RANGES)
    avoid_fire_bonus = 1 if has_shen_yunting and player.talisman_avoid_fire > 0 else 0
    break_armor_bonus = 1 if player.talisman_break_armor > 0 else 0
    owned_effects = guard_bonus + fire_bonus + avoid_fire_bonus + break_armor_bonus
    return min(2, (owned_effects + 1) // 2)


def _intel_bonus(player: Player, section: str, cap_value: int = 2) -> int:
    bonus = int(player.heishui_tournament_bonuses.get(section, 0))
    return max(-cap_value, min(cap_value, bonus))


def _mixed_resource_reserve(player: Player) -> int:
    herbal_reserve = (
        max(0, int(getattr(player, "herbs", 0))) // 25
        + max(0, int(getattr(player, "aged_herbs_10", 0))) // 3
        + max(0, int(getattr(player, "aged_herbs_30", 0)))
    )
    pill_reserve = max(0, int(getattr(player, "pills", 0))) // 4
    return min(2, herbal_reserve + pill_reserve)


def _mixed_adaptive_relief(player: Player, breadth: int) -> int:
    if breadth < 3:
        return 0
    mixed_points = max(0, int(getattr(player, "mixed_practice_points", 0)))
    diverse_months = max(0, int(getattr(player, "diverse_action_months", 0)))
    adaptive_exp = max(0, int(getattr(player, "adaptive_experience", 0)))
    mixed_path_score = max(0, int(getattr(player, "mixed_path_score", 0)))
    resource_reserve = _mixed_resource_reserve(player)

    relief = 0
    if mixed_points >= 4 and diverse_months >= 2:
        relief += 1
    if adaptive_exp >= 4:
        relief += 1
    relief += resource_reserve
    if mixed_path_score >= 2 and diverse_months >= 1:
        relief += 1

    risk_load = 0
    if (
        int(getattr(player, "theft_attempts", 0)) >= 3
        or int(getattr(player, "theft_trace_level", 0)) >= 2
        or int(getattr(player, "theft_suspicion_level", 0)) >= 2
    ):
        risk_load += 1
    if (
        int(getattr(player, "heishui_purchase_count", 0)) >= 3
        or int(getattr(player, "tracking_marks", 0)) > 0
        or int(getattr(player, "blackwater_debt", 0)) > 0
        or int(getattr(player, "blackwater_trace_level", 0)) > 0
    ):
        risk_load += 1
    if (
        int(getattr(player, "demonic_qi", 0)) >= 20
        or int(getattr(player, "karma", 0)) >= 15
        or int(getattr(player, "demonic_contamination", 0)) > 0
    ):
        risk_load += 1

    if resource_reserve <= 0:
        relief = 1 if mixed_path_score >= 3 and diverse_months >= 2 else 0
    else:
        relief = min(relief, resource_reserve + 1)
    return min(2, max(0, relief - risk_load))


def _practice_pressure_adjustments(player: Player) -> Dict[str, object]:
    fatigue = max(0, int(getattr(player, "meditation_fatigue", 0)))
    closed_months = max(0, int(getattr(player, "closed_training_months", 0)))
    pressure = max(0, int(getattr(player, "cultivation_pressure", 0)))
    breadth = calculate_breadth(player)
    stones = max(0, int(getattr(player, "spirit_stones", 0)))
    narrow_penalty = 1 if closed_months >= 6 and breadth <= 2 else 0
    resource_squeeze = 0
    if breadth >= 4 and int(getattr(player, "foundation", 0)) >= 50 and stones < 5:
        resource_squeeze = 3 if stones <= 1 else 1

    pressure_drag = 1 if pressure > 0 else 0
    mind_penalty = min(2, fatigue // 20 + (1 if pressure >= 4 else 0))
    trial_penalty = min(4, closed_months // 11 + pressure_drag + pressure // 4 + narrow_penalty + resource_squeeze)
    combat_penalty = min(4, fatigue // 20 + closed_months // 12 + pressure_drag + pressure // 5 + resource_squeeze)
    adaptive_relief = _mixed_adaptive_relief(player, breadth)
    trial_penalty = max(0, trial_penalty - min(2, adaptive_relief))
    combat_penalty = max(0, combat_penalty - min(1, max(0, adaptive_relief - 1)))

    notes: List[str] = []
    if fatigue >= 6:
        notes.append("冥坐疲劳：连月闭门打坐，问心与斗法发挥略滞。")
    if closed_months >= 6 and breadth <= 2:
        notes.append("闭门偏科：修为稳固，但山门试炼与斗法应变不足。")
    if pressure > 0:
        notes.append("修行缺口：诸艺并修的耗材与人情未补齐，临场准备受损。")
    if resource_squeeze:
        notes.append("资源紧绷：根基与诸艺铺得太开，临近大比时调度余裕不足。")
    if adaptive_relief:
        notes.append("杂学傍身：多线经验与资源预案缓和了临场扣分。")

    return {
        "mind": -mind_penalty,
        "trial": -trial_penalty,
        "combat": -combat_penalty,
        "total": -(mind_penalty + trial_penalty + combat_penalty),
        "adaptive_relief": adaptive_relief,
        "notes": notes,
    }


def run_tournament(player: Player) -> Dict[str, object]:
    final_month_summary = ""
    pre_tournament_event_logs: List[Dict[str, object]] = []
    playtest_logging = not bool(getattr(player, "_suppress_playtest_logging", False))
    try:
        event_rng = random.Random(120000 + int(getattr(player, "total_actions", 0)) + len(getattr(player, "triggered_event_ids", []) or []))
        pre_tournament_event_logs = process_chapter1_monthly_events(player, 12, interactive=False, rng=event_rng, force=True)
        if (
            playtest_logging
            and player.finished
            and not any(int(entry.get("month", 0)) == 12 for entry in getattr(player, "monthly_summary_log", []) or [])
        ):
            event_titles = [str(entry.get("title", "")) for entry in pre_tournament_event_logs if entry.get("title")]
            if not event_titles:
                event_titles = ["一年期满，家族大比开场"]
            final_month_summary = str(
                summarize_month(player, 12, events=event_titles).get("text", "")
            )
    except Exception:
        pre_tournament_event_logs = []
        final_month_summary = ""

    mind_intel_bonus = _intel_bonus(player, "mind")
    trial_intel_bonus = _intel_bonus(player, "trial")
    combat_intel_bonus = _intel_bonus(player, "combat")
    theft_adjustments = theft_tournament_adjustments(player)
    theft_mind = int(theft_adjustments.get("mind", 0))
    theft_trial = int(theft_adjustments.get("trial", 0))
    theft_combat = int(theft_adjustments.get("combat", 0))
    growth_adjustments = growth_tournament_adjustments(player)
    growth_mind = int(growth_adjustments.get("mind", 0))
    growth_trial = int(growth_adjustments.get("trial", 0))
    growth_combat = int(growth_adjustments.get("combat", 0))
    practice_adjustments = _practice_pressure_adjustments(player)
    practice_mind = int(practice_adjustments.get("mind", 0))
    practice_trial = int(practice_adjustments.get("trial", 0))
    practice_combat = int(practice_adjustments.get("combat", 0))
    burst = foundation_burst_bonus(player)
    burst_mind = int(burst.get("mind", 0))
    burst_trial = int(burst.get("trial", 0))
    burst_combat = int(burst.get("combat", 0))
    attack = player.attack + equipment_bonus(player, "attack_bonus")
    defense = player.defense + equipment_bonus(player, "defense_bonus")
    speed = player.speed + equipment_bonus(player, "speed_bonus")
    physique = player.physique
    mp = player.mp
    dao_heart = player.dao_heart + equipment_bonus(player, "dao_heart_bonus")
    divine_sense = player.divine_sense + equipment_bonus(player, "divine_sense_bonus")
    exposure = max(0, player.exposure + equipment_bonus(player, "exposure_bonus"))
    heart_demon = max(0, player.heart_demon + equipment_bonus(player, "heart_demon_bonus"))
    karma = max(0, player.karma + equipment_bonus(player, "karma_bonus"))
    alchemy_reserve_bonus = min(
        9,
        player.pills
        + furnace_level(player)
        + min(2, player.spirit_field_harvest_count)
        + material_total(player) // 2,
    )
    mind_score = _cap(
        player.realm_level * 2
        + player.cultivation_progress // 15
        + player.root_growth
        + dao_heart // 2
        + divine_sense
        + min(player.pills, 5)
        + player.righteous_reputation // 8
        - heart_demon // 3
        - player.demonic_qi // 4
        - karma // 4
        - max(0, exposure - 50) // 8
        + mind_intel_bonus
        + theft_mind
        + growth_mind
        + practice_mind
        + burst_mind,
        25,
    )
    trial_score = _cap(
        physique
        + speed // 2
        + player.luck
        + player.intelligence // 5
        + min(player.herbs, 12) // 4
        + player.aged_herbs_10
        + player.aged_herbs_30 * 2
        + player.contribution // 4
        + min(player.spirit_stones // 10, 3)
        + alchemy_reserve_bonus
        - exposure // 4
        - heart_demon // 8
        - karma // 8
        + trial_intel_bonus
        + theft_trial
        + growth_trial
        + practice_trial
        + burst_trial,
        35,
    )
    talisman_bonus = _talisman_combat_bonus(player)
    combat_score = _cap(
        attack // 3
        + defense // 2
        + speed // 2
        + mp // 12
        + player.combat_exp // 3
        + player.intelligence // 8
        + min(player.pills, 5)
        + min(player.souls_refined, 4)
        + talisman_bonus
        - heart_demon // 5
        - player.demonic_qi // 3
        - karma // 3
        - max(0, exposure - 35) // 6
        + combat_intel_bonus
        + theft_combat
        + growth_combat
        + practice_combat
        + burst_combat,
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
    if equipment_bonus(player, "exposure_bonus") > 1 or equipment_bonus(player, "karma_bonus") > 1:
        flags.append("旧器留痕")
    if player.average_affection() >= 35:
        flags.append("旁支有人")
    if player.intelligence >= 20:
        flags.append("情报先手")
    for flag in theft_adjustments.get("flags", []):
        if str(flag) not in flags:
            flags.append(str(flag))

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

    reward_text = ""
    if rank == 1:
        reward_item = grant_equipment(player, "greenwood_sword")
        reward_text = f"大比奖励：族中赐下{reward_item}。" if reward_item else ""
    elif rank <= 3:
        reward_item = grant_equipment(player, "sense_charm")
        reward_text = f"大比奖励：族中赐下{reward_item}。" if reward_item else ""
    elif top_ten:
        reward_item = grant_equipment(player, "shen_training_robe")
        reward_text = f"大比奖励：族中赐下{reward_item}。" if reward_item else ""

    player.ending_flags = flags
    player.clamp()
    result = {
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
        "theft_tournament_adjustment": int(theft_adjustments.get("total", 0)),
        "theft_tournament_notes": list(theft_adjustments.get("notes", [])),
        "growth_tournament_adjustment": int(growth_adjustments.get("total", 0)),
        "growth_tournament_notes": list(growth_adjustments.get("notes", [])),
        "practice_pressure_adjustment": int(practice_adjustments.get("total", 0)),
        "mixed_adaptive_relief": int(practice_adjustments.get("adaptive_relief", 0)),
        "practice_pressure_notes": list(practice_adjustments.get("notes", [])),
        "foundation_burst_bonus": int(burst.get("total", 0)),
        "foundation_burst_triggered": bool(burst.get("triggered", False)),
        "foundation_burst_text": str(burst.get("text", "")),
        "foundation": player.foundation,
        "breadth": calculate_breadth(player),
        "equipment_score": equipment_score(player),
        "alchemy_reserve_bonus": alchemy_reserve_bonus,
        "reward_text": reward_text,
        "pre_tournament_event_logs": pre_tournament_event_logs,
        "final_month_summary": final_month_summary,
    }
    if playtest_logging:
        try:
            result["playtest_report"] = format_playtest_report(player, result)
        except Exception:
            result["playtest_report"] = ""
    else:
        result["playtest_report"] = ""
    return result


def format_tournament_result(result: Dict[str, object]) -> str:
    lines = ["\n===== 青岭沈家家族大比 ====="]
    lines.append("评分：100分制")
    scores = result["scores"]
    if isinstance(scores, dict):
        lines.append(f"测灵问心：{scores.get('测灵问心', 0)}/25")
        lines.append(f"百药山试炼：{scores.get('百药山试炼', 0)}/35")
        lines.append(f"斗法台：{scores.get('斗法台', 0)}/40")
    lines.append(f"符箓斗法加成：+{result.get('talisman_bonus', 0)}")
    if result.get("alchemy_reserve_bonus", 0):
        lines.append(f"炼丹筹备加成：+{int(result.get('alchemy_reserve_bonus', 0))}")
    if result.get("equipment_score", 0):
        lines.append(f"装备评分：{int(result.get('equipment_score', 0))}")
    if result.get("heishui_intel_bonus", 0):
        lines.append(f"黑水情报修正：{int(result.get('heishui_intel_bonus', 0)):+d}")
    if result.get("theft_tournament_adjustment", 0):
        lines.append(f"盗术综合修正：{int(result.get('theft_tournament_adjustment', 0)):+d}")
    if result.get("growth_tournament_adjustment", 0):
        lines.append(f"根基融会修正：{int(result.get('growth_tournament_adjustment', 0)):+d}")
    if result.get("practice_pressure_adjustment", 0):
        lines.append(f"闭关与资源修正：{int(result.get('practice_pressure_adjustment', 0)):+d}")
    if result.get("foundation_burst_triggered", False):
        lines.append(f"厚积薄发修正：+{int(result.get('foundation_burst_bonus', 0))}")
        burst_text = str(result.get("foundation_burst_text", ""))
        if burst_text:
            lines.append(burst_text)
    theft_notes = result.get("theft_tournament_notes", [])
    if isinstance(theft_notes, list) and theft_notes:
        lines.append("盗术评价：")
        for note in theft_notes:
            lines.append(f"- {note}")
    growth_notes = result.get("growth_tournament_notes", [])
    if isinstance(growth_notes, list) and growth_notes:
        lines.append("根基融会：")
        for note in growth_notes:
            lines.append(f"- {note}")
    practice_notes = result.get("practice_pressure_notes", [])
    if isinstance(practice_notes, list) and practice_notes:
        lines.append("闭关与资源压力：")
        for note in practice_notes:
            lines.append(f"- {note}")
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
    if result.get("reward_text"):
        lines.append(str(result["reward_text"]))
    pre_tournament_logs = result.get("pre_tournament_event_logs", [])
    if isinstance(pre_tournament_logs, list):
        for log_entry in pre_tournament_logs:
            if isinstance(log_entry, dict):
                lines.append(format_chapter1_event_log(log_entry))
    if result.get("final_month_summary"):
        lines.append(str(result["final_month_summary"]))
    playtest_report = str(result.get("playtest_report", ""))
    if playtest_report:
        lines.append(playtest_report)
    return "\n".join(lines)
