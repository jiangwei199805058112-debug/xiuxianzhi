"""第一章行动系统。"""

from __future__ import annotations

import random
from typing import Callable, Dict, List

from data import ACTION_NAMES, ATTRIBUTE_NAMES, MARKET_GOODS, MARKET_PRICES, MONTHLY_EVENTS, NPCS
from heishui_market import market_action as heishui_market_action, resolve_monthly_risk_event
from player import Player


def action_menu_text() -> str:
    lines = ["可选行动："]
    for key, name in ACTION_NAMES.items():
        lines.append(f"{key}. {name}")
    lines.append("S. 存档")
    lines.append("L. 读档")
    lines.append("Q. 退出")
    return "\n".join(lines)


def _roll(low: int, high: int) -> int:
    return random.randint(low, high)


def _read_choice(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def _choose_npc(prompt: str) -> str:
    names = list(NPCS)
    print(prompt)
    for index, name in enumerate(names, start=1):
        print(f"{index}. {name}：{NPCS[name]}")
    choice = _read_choice("请选择对象：")
    if choice.isdigit():
        index = int(choice)
        if 1 <= index <= len(names):
            return names[index - 1]
    print("你一时拿不定主意，最后去见了沈若兰。")
    return names[0]


def _jade_bottle_text(player: Player) -> str:
    if not player.has_jade_bottle:
        return "你尚未得到古玉瓶，无法催熟灵草。"

    print("古玉瓶可催熟灵草：")
    print("1. 少量：消耗1灵石，十年份灵草+1，暴露度+3")
    print("2. 中量：消耗2灵石，十年份灵草+2，暴露度+8")
    print("3. 大量：消耗3灵石，三十年份灵草+1，暴露度+15")
    print("0. 暂不使用")
    choice = _read_choice("请选择古玉瓶用量：")

    plans = {
        "1": ("少量", 1, "aged_herbs_10", 1, 3),
        "2": ("中量", 2, "aged_herbs_10", 2, 8),
        "3": ("大量", 3, "aged_herbs_30", 1, 15),
    }
    plan = plans.get(choice)
    if plan is None:
        return "你没有动用古玉瓶，只按寻常法子照看药田。"

    label, cost, herb_attr, herb_gain, exposure_gain = plan
    if player.spirit_stones < cost:
        return f"你想动用古玉瓶的{label}催熟，但灵石不足。"

    player.spirit_stones -= cost
    setattr(player, herb_attr, getattr(player, herb_attr) + herb_gain)
    player.exposure += exposure_gain
    player.clamp()
    herb_name = "十年份灵草" if herb_attr == "aged_herbs_10" else "三十年份灵草"
    return f"你动用古玉瓶{label}催熟，消耗灵石{cost}，{herb_name}+{herb_gain}，暴露度+{exposure_gain}。"


def action_cultivate(player: Player) -> str:
    before_realm = player.realm_level
    gain = _roll(4, 7) + max(1, player.cultivation_speed // 2) + player.root_growth
    used_pill = False
    if player.pills > 0:
        player.pills -= 1
        gain += _roll(5, 8)
        player.heart_demon += 1
        used_pill = True
    player.gain_cultivation_progress(gain)
    if random.random() < 0.35:
        player.dao_heart += 1
    player.heart_demon += _roll(0, 1)
    player.exposure += 1 if gain >= 13 else 0
    player.clamp()
    pill_text = "你服下一枚丹药，药力推着灵气贯通周天。" if used_pill else "你没有丹药辅佐，只靠吐纳打磨根基。"
    realm_text = f"境界突破至{player.realm_name()}。" if player.realm_level > before_realm else ""
    return f"你打坐修炼一旬。{pill_text}修炼进度提升 {gain}。{realm_text}"


def action_spirit_field(player: Player) -> str:
    contribution_gain = _roll(2, 4)
    herb_gain = _roll(1, 3)
    player.contribution += contribution_gain
    player.herbs += herb_gain
    player.righteous_reputation += 1
    player.npc_affection["沈若兰"] += 2

    if not player.has_jade_bottle:
        player.has_jade_bottle = True
        player.clamp()
        return (
            f"你第一次照看药田，得普通灵草{herb_gain}，家族贡献+{contribution_gain}。"
            "收工时，你在旧药渠下捡到一只温润古玉瓶。古玉瓶已获得。"
        )

    bottle_text = _jade_bottle_text(player)
    player.clamp()
    return (
        f"你照看药田，得普通灵草{herb_gain}，家族贡献+{contribution_gain}。"
        f"沈若兰对你印象稍好。{bottle_text}"
    )


def action_gather_herbs(player: Player) -> str:
    herb_gain = _roll(1, 5)
    stone_gain = _roll(0, 1)
    intel_text = ""
    if player.explore_intel_bonus > 0:
        player.explore_intel_bonus -= 1
        herb_gain += 1
        stone_gain += 1 if random.random() < 0.70 else 0
        player.exposure = max(0, player.exposure - 1)
        intel_text = "你按天机阁情报避开险路，多采了几处隐蔽药丛。"
    if random.random() < 0.12:
        herb_gain = max(0, herb_gain - 1)
        player.exposure += 1
        player.hp -= _roll(1, 3)
        setback_text = "山中药点被人采过，你绕了远路，收获不稳。"
    else:
        setback_text = ""
    player.herbs += herb_gain
    player.spirit_stones += stone_gain
    player.physique += 1 if random.random() < 0.85 else 0
    player.luck += 1 if random.random() < 0.12 else 0
    player.exposure += 1
    player.hp -= _roll(0, 4)

    if random.random() < 0.35:
        player.exposure += 2
        trail_text = "回程时你被巡山族人问了几句，暴露度略升。"
    else:
        trail_text = "你避开人多的山道，顺利回到旁支小院。"

    cave_text = ""
    if not player.has_soul_banner and random.random() < 0.05:
        player.has_soul_banner = True
        player.demonic_qi += 3
        cave_text = "你在百药山深处发现隐秘山洞，探索后取得一面残破魂幡。"

    player.clamp()
    return f"你入百药山采药，得到普通灵草{herb_gain}，灵石{stone_gain}。{intel_text}{setback_text}{trail_text}{cave_text}"


def action_family_work(player: Player) -> str:
    contribution_gain = _roll(3, 5)
    stone_gain = _roll(1, 3)
    player.contribution += contribution_gain
    player.spirit_stones += stone_gain
    player.righteous_reputation += 2
    player.heart_demon -= 1
    player.npc_affection["沈怀安"] += 2
    player.clamp()
    return f"你接下家族杂务，跑腿、抄册、守夜皆做，家族贡献+{contribution_gain}，灵石+{stone_gain}。"


def _sell_aged_herb(player: Player, attr: str, label: str, price: int) -> str:
    if getattr(player, attr) <= 0:
        return f"你没有可出售的{label}。"

    setattr(player, attr, getattr(player, attr) - 1)
    if player.aged_herbs_sold_this_month < 3:
        player.aged_herbs_sold_this_month += 1
        player.spirit_stones += price
        player.clamp()
        return f"你按正常行情出售1株{label}，灵石+{price}。本月高年份灵草正常出售{player.aged_herbs_sold_this_month}/3。"

    black_price = price * 60 // 100
    player.spirit_stones += black_price
    player.exposure += 5
    player.clamp()
    return f"正常渠道已满，你转走黑市出售1株{label}，灵石+{black_price}，暴露度+5。"


def _apply_market_good(player: Player, good: Dict[str, object]) -> None:
    effects = good.get("effects", {})
    if not isinstance(effects, dict):
        return
    for attr, value in effects.items():
        if not isinstance(attr, str):
            continue
        if attr == "hp":
            player.hp = min(player.max_hp, player.hp + int(value))
        else:
            setattr(player, attr, getattr(player, attr) + int(value))
    player.clamp()


def _buy_market_good(player: Player) -> str:
    print("坊市货摊：")
    for index, good in enumerate(MARKET_GOODS, start=1):
        print(f"{index}. {good['name']}：{good['price']}灵石｜效果：{good['effect_text']}")
    print("0. 返回")
    choice = _read_choice("请选择商品：")
    if not choice.isdigit():
        return "你没有买东西，只在摊前看了几眼。"

    index = int(choice)
    if index == 0:
        return "你离开货摊，没有买东西。"
    if index < 1 or index > len(MARKET_GOODS):
        return "坊市里没有这件商品。"

    good = MARKET_GOODS[index - 1]
    price = int(good["price"])
    if player.spirit_stones < price:
        return f"你灵石不足，买不起{good['name']}。"

    player.spirit_stones -= price
    _apply_market_good(player, good)
    return f"你买下{good['name']}，花费灵石{price}。效果：{good['effect_text']}。"


def _sell_herbs_market(player: Player) -> str:
    normal_price = MARKET_PRICES["普通灵草"]
    ten_price = MARKET_PRICES["十年份灵草"]
    thirty_price = MARKET_PRICES["三十年份灵草"]
    print("出售灵草，每次行动出售一株：")
    print(f"1. 普通灵草：{normal_price}灵石")
    print(f"2. 十年份灵草：{ten_price}灵石，超额走黑市")
    print(f"3. 三十年份灵草：{thirty_price}灵石，超额走黑市")
    print("0. 返回")
    print(f"本月高年份灵草正常出售：{player.aged_herbs_sold_this_month}/3")
    choice = _read_choice("请选择出售项：")

    if choice == "1":
        if player.herbs <= 0:
            return "你没有可出售的普通灵草。"
        player.herbs -= 1
        player.spirit_stones += normal_price
        player.clamp()
        return "你出售1株普通灵草，灵石+2。"
    if choice == "2":
        return _sell_aged_herb(player, "aged_herbs_10", "十年份灵草", ten_price)
    if choice == "3":
        return _sell_aged_herb(player, "aged_herbs_30", "三十年份灵草", thirty_price)
    if choice == "0":
        return "你没有出售灵草。"
    return "坊市牙人没听懂你的意思，交易作罢。"


def action_market(player: Player) -> str:
    print("坊市交易：")
    print("A. 买入商品")
    print("B. 出售灵草")
    print("C. 打听行情，情报值+1")
    print("D. 黑水坊市")
    print("E. 离开坊市")
    choice = _read_choice("请选择：").upper()

    if choice == "A":
        return _buy_market_good(player)
    if choice == "B":
        return _sell_herbs_market(player)
    if choice == "C":
        if random.random() < 0.75:
            player.intelligence += 1
            result = "你在坊市茶棚打听行情，情报值+1。"
        else:
            result = "你在坊市茶棚听了半日传闻，却没筛出可用消息。"
        player.clamp()
        return result
    if choice == "D":
        return heishui_market_action(player)
    if choice == "E":
        return "你离开坊市，没有交易。"

    if random.random() < 0.65:
        player.intelligence += 1
        result = "你没选定交易，只在坊市听了半日行情，情报值+1。"
    else:
        result = "你没选定交易，只听到几句过时行情。"
    player.clamp()
    return result


def action_refine_pills(player: Player) -> str:
    if player.herbs >= 4 and player.spirit_stones >= 2:
        player.herbs -= 4
        player.spirit_stones -= 2
        if random.random() < 0.15:
            player.heart_demon += 2
            player.exposure += 3
            player.hp -= 5
            player.clamp()
            return "你关门偷偷炼丹，却因火候不稳炸了小炉。消耗普通灵草4株和灵石2枚，心魔值+2，暴露度+3，气血-5。"
        made = _roll(2, 4)
        player.pills += made
        player.comprehension += 1
        player.heart_demon += 1
        player.exposure += 2
        player.hp -= 2
        player.clamp()
        return f"你关门偷偷炼丹，消耗普通灵草4株和灵石2枚，得到丹药{made}枚。丹毒入体，心魔值+1，暴露度+2，气血-2。"

    if player.aged_herbs_10 >= 1 and player.spirit_stones >= 3:
        player.aged_herbs_10 -= 1
        player.spirit_stones -= 3
        if random.random() < 0.10:
            player.heart_demon += 3
            player.exposure += 4
            player.hp -= 7
            player.clamp()
            return "你用十年份灵草偷偷炼丹，药力反冲，经脉灼痛。心魔值+3，暴露度+4，气血-7。"
        made = _roll(3, 5)
        player.pills += made
        player.comprehension += 1
        player.heart_demon += 2
        player.exposure += 4
        player.hp -= 3
        player.clamp()
        return f"你用十年份灵草偷偷炼丹，得到丹药{made}枚。丹毒更烈，心魔值+2，暴露度+4，气血-3。"

    player.contribution += 1
    player.npc_affection["沈若兰"] += 1
    player.clamp()
    return "材料不足，你改去丹房外围帮忙分拣药材，家族贡献+1，沈若兰好感+1。"


def action_visit_npc(player: Player) -> str:
    npc = _choose_npc("你准备结交哪位族人？")
    affection_gain = _roll(3, 6) + player.charm // 4
    player.npc_affection[npc] += affection_gain
    if npc == "沈若兰":
        player.herbs += 1
    elif npc == "沈云庭":
        player.combat_exp += 2
        player.heart_demon += 1
    elif npc == "沈子岳":
        player.combat_exp += 1
        player.charm += 1
    elif npc == "沈怀安":
        player.contribution += 1
        player.intelligence += 1
    elif npc == "沈霜":
        player.intelligence += 2
        player.divine_sense += 1
    elif npc == "沈墨阳":
        player.intelligence += 2
        player.demonic_qi += 1
    player.clamp()
    return f"你寻机结交{npc}，好感提升{affection_gain}。"


def action_spell_training(player: Player) -> str:
    fatigued = player.hp < player.max_hp * 55 // 100
    if fatigued:
        attack_gain = 1 if random.random() < 0.45 else 0
        mp_gain = _roll(0, 1)
        combat_gain = 1 if random.random() < 0.45 else 0
    else:
        attack_gain = _roll(1, 2)
        mp_gain = _roll(1, 3)
        combat_gain = _roll(1, 2)
    player.attack += attack_gain
    player.mp += mp_gain
    player.combat_exp += combat_gain
    if fatigued:
        player.divine_sense += 1 if random.random() < 0.70 else 0
    else:
        player.divine_sense += 1
    player.hp -= _roll(1, 4)
    player.heart_demon += 1 if random.random() < (0.50 if fatigued else 0.35) else 0
    player.clamp()
    fatigue_text = "勉强练习，疲态已显。" if fatigued else ""
    return f"你修炼基础法术，{fatigue_text}攻击+{attack_gain}，灵力+{mp_gain}，斗法经验+{combat_gain}，气血略损。"


def action_investigate(player: Player) -> str:
    if random.random() < 0.10:
        gain = 0
        false_text = "线人给的消息互相矛盾，暂时没有可用情报。"
    else:
        gain = _roll(2, 3)
        false_text = ""
    player.intelligence += gain
    player.exposure += 1
    if random.random() < 0.35:
        player.exposure += 1
    if random.random() < 0.25:
        player.heart_demon += 1
    player.npc_affection["沈霜"] += 1
    player.clamp()
    return f"你探查大比签表、试炼药点与对手习惯，情报值+{gain}，暴露度+1。{false_text}沈霜对你的细心略有改观。"


def action_soul_banner(player: Player) -> str:
    if not player.has_soul_banner:
        player.exposure += 1
        player.clamp()
        return "你尚未得到残破魂幡，只能在夜色里空守一场，无法暗中炼魂。"

    refine_gain = _roll(1, 2)
    combat_gain = _roll(2, 4)
    attack_gain = _roll(1, 3)
    progress_gain = _roll(4, 8)
    player.souls_refined += refine_gain
    player.combat_exp += combat_gain
    player.attack += attack_gain
    player.gain_cultivation_progress(progress_gain)
    player.demonic_qi += _roll(10, 15)
    player.karma += _roll(9, 14)
    player.heart_demon += _roll(8, 12)
    player.righteous_reputation -= 4
    player.exposure += _roll(8, 12)
    if player.souls_refined >= 3 or random.random() < 0.35:
        player.exposure += _roll(6, 10)
        player.karma += _roll(3, 6)
        player.heart_demon += _roll(3, 6)
    player.clamp()
    return (
        "你以残破魂幡收拢游魂，只敢炼化最浅的一缕阴气。"
        f"修炼进度+{progress_gain}，攻击+{attack_gain}，斗法经验+{combat_gain}，炼魂次数+{refine_gain}。"
    )


def action_romance(player: Player) -> str:
    npc = _choose_npc("你准备与谁进行情缘互动？")
    affection_gain = _roll(3, 6) + player.charm // 3 + player.love_lock_level
    player.npc_affection[npc] += affection_gain
    player.charm += 1
    player.dao_heart += 1 if player.npc_affection[npc] >= 30 else 0
    player.heart_demon += _roll(0, 2)
    player.karma += 1
    player.exposure += 1
    player.clamp()
    return (
        f"你以情意锁低阶残印辅助言谈，只牵引一丝亲近感。{npc}好感提升{affection_gain}，"
        "魅力+1，业力+1。"
    )


def action_meditate(player: Player) -> str:
    heart_drop = _roll(2, 4)
    demonic_drop = _roll(0, 2)
    exposure_drop = _roll(0, 2)
    player.heart_demon -= heart_drop
    player.demonic_qi -= demonic_drop
    player.exposure -= exposure_drop
    player.dao_heart += 1
    player.righteous_reputation += 1
    player.clamp()
    return f"你焚香静坐，压下杂念。心魔值-{heart_drop}，魔气值-{demonic_drop}，暴露度-{exposure_drop}，道心+1。"


ACTION_HANDLERS: Dict[str, Callable[[Player], str]] = {
    "1": action_cultivate,
    "2": action_spirit_field,
    "3": action_gather_herbs,
    "4": action_family_work,
    "5": action_market,
    "6": action_refine_pills,
    "7": action_visit_npc,
    "8": action_spell_training,
    "9": action_investigate,
    "10": action_soul_banner,
    "11": action_romance,
    "12": action_meditate,
}


def perform_action(player: Player, choice: str) -> str:
    handler = ACTION_HANDLERS.get(choice)
    if handler is None:
        return "无效行动。"
    result = handler(player)
    player.advance_action()
    return result


def monthly_event(player: Player) -> str:
    player.aged_herbs_sold_this_month = 0
    event = random.choice(MONTHLY_EVENTS)
    for attr, value in event["effects"].items():
        setattr(player, attr, getattr(player, attr) + int(value))
    heishui_text = resolve_monthly_risk_event(player)
    player.clamp()
    effects_text = "，".join(
        f"{ATTRIBUTE_NAMES.get(key, key)}{value:+d}" for key, value in event["effects"].items()
    )
    lines = [
        f"月末事件：{event['title']}",
        str(event["text"]),
        f"影响：{effects_text}",
    ]
    if heishui_text:
        lines.append(heishui_text)
    lines.append("本月高年份灵草正常出售次数已重置。")
    return "\n".join(lines)


def risk_summary(player: Player) -> List[str]:
    warnings: List[str] = []
    if player.has_jade_bottle and player.exposure >= 60:
        warnings.append("古玉瓶的异常收益已接近被族中察觉。")
    if player.heart_demon >= 70:
        warnings.append("心魔深重，可能拖累大比问心评分。")
    if player.has_soul_banner and player.demonic_qi >= 45:
        warnings.append("残破魂幡带来的魔气已经难以完全遮掩。")
    if player.karma >= 50:
        warnings.append("业力过重，隐藏线结局风险升高。")
    if player.tracking_marks > 0:
        warnings.append("你在黑水坊市留下了追踪痕迹，月末可能招来麻烦。")
    return warnings
