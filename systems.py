"""第一章行动系统。"""

from __future__ import annotations

import random
from typing import Callable, Dict, List

from cultivation_assets import (
    MATERIAL_NAMES,
    advance_spirit_fields,
    buy_equipment,
    buy_furnace,
    buy_seed_pack,
    consume_alchemy_materials,
    current_furnace,
    equip_item,
    equipment_inventory_text,
    equipment_shop_text,
    equipment_status_text,
    field_status_text,
    furnace_shop_text,
    furnace_status_text,
    grant_equipment,
    harvest_all_fields,
    material_total,
    one_click_plant,
    tend_all_fields,
    upgrade_spirit_field,
)
from data import ACTION_NAMES, ATTRIBUTE_NAMES, MARKET_GOODS, MARKET_PRICES, MONTHLY_EVENTS, NPCS
from heishui_market import market_action as heishui_market_action, resolve_monthly_risk_event
from player import Player


def action_menu_text() -> str:
    lines = ["可选行动："]
    for key, name in ACTION_NAMES.items():
        lines.append(f"{key}. {name}")
    lines.append("L. 读档")
    lines.append("S/Q 仍可作为存档/退出快捷键。")
    return "\n".join(lines)


def _roll(low: int, high: int) -> int:
    return random.randint(low, high)


def _read_choice(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def tutorial_tip(player: Player) -> str:
    flags = player.tutorial_flags
    if player.month == 1 and "tutorial_month_1" not in flags:
        flags.append("tutorial_month_1")
        player.clamp()
        return (
            "【族中老人提醒】\n"
            "单靠打坐最为稳妥，却难在家族大比中出头。\n"
            "若想冲榜，丹药、符箓、情报、灵田、装备皆可助你一程。\n"
            "只是捷径多伴风险，黑水坊市尤其如此。"
        )
    if player.month == 2 and "tutorial_month_2" not in flags:
        flags.append("tutorial_month_2")
        player.clamp()
        return (
            "【族中老人补充】\n"
            "丹毒、心魔、暴露积得太高，到了大比问心和斗法台都会拖后腿。\n"
            "魔道与黑水坊市能换来快收益，也更容易留下后患。"
        )
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

    equipment_text = ""
    if random.random() < 0.025:
        item_id = random.choice(["calm_charm", "cloth_boots", "iron_sword"])
        item_name = grant_equipment(player, item_id)
        if item_name:
            equipment_text = f"返程时你在乱石间捡到一件旧物：{item_name}。"

    player.clamp()
    return (
        f"你入百药山采药，得到普通灵草{herb_gain}，灵石{stone_gain}。"
        f"{intel_text}{setback_text}{trail_text}{cave_text}{equipment_text}"
    )


def action_family_work(player: Player) -> str:
    contribution_gain = _roll(3, 5)
    stone_gain = _roll(1, 3)
    player.contribution += contribution_gain
    player.spirit_stones += stone_gain
    player.righteous_reputation += 2
    player.heart_demon -= 1
    player.npc_affection["沈怀安"] += 2
    equipment_text = ""
    if random.random() < 0.025:
        item_name = grant_equipment(player, "patched_robe")
        if item_name:
            equipment_text = f"一位族中长辈见你做事踏实，顺手赠你{item_name}。"
    player.clamp()
    return (
        f"你接下家族杂务，跑腿、抄册、守夜皆做，家族贡献+{contribution_gain}，灵石+{stone_gain}。"
        f"{equipment_text}"
    )


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
    print("E. 挑选基础装备")
    print("F. 离开坊市")
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
        print(equipment_shop_text())
        selected = _read_choice("请选择购买装备：")
        return buy_equipment(player, int(selected)) if selected.isdigit() else "你没有购买装备。"
    if choice == "F":
        return "你离开坊市，没有交易。"

    if random.random() < 0.65:
        player.intelligence += 1
        result = "你没选定交易，只在坊市听了半日行情，情报值+1。"
    else:
        result = "你没选定交易，只听到几句过时行情。"
    player.clamp()
    return result


def _furnace_fire_text(furnace: Dict[str, object]) -> str:
    furnace_id = str(furnace.get("furnace_id", "none"))
    if furnace_id == "worn_furnace":
        return "破旧丹炉炉壁微颤，火候时稳时散。"
    if furnace_id == "bronze_furnace":
        return "青铜丹炉聚火较稳，药液翻涌得有章法。"
    if furnace_id == "black_iron_furnace":
        return "玄铁丹炉火力沉厚，炉腹深处隐有低鸣。"
    return "简陋火盆火舌忽明忽暗，你只能凭经验控火。"


def _alchemy_success_text(
    furnace: Dict[str, object],
    made: int,
    max_made: int,
    heart_gain: int,
    exposure_gain: int,
) -> str:
    if made >= max_made and heart_gain == 0:
        result = "丹炉火候恰到好处，药香四溢，这一炉成色极佳。"
    elif heart_gain > 0:
        result = "炉中药力躁动，你强行压制，虽成丹却染上些许丹毒。"
    else:
        result = "丹炉火候略稳，这一炉丹药成色尚可。"
    if str(furnace.get("furnace_id")) == "black_iron_furnace" and exposure_gain > 0:
        result += "玄铁丹炉火力太盛，动静不小，似乎引来旁人注意。"
    return result


def _alchemy_failure_text(furnace: Dict[str, object], severe: bool) -> str:
    if severe:
        result = "丹火一乱，药材尽数化作焦灰，只余一缕苦味。"
    else:
        result = "丹火稍有不稳，部分药材化为焦灰，你及时压住炉火才没闹出更大动静。"
    if str(furnace.get("furnace_id")) == "black_iron_furnace":
        result += "玄铁丹炉余火沉闷，屋外似有人驻足片刻。"
    return result


def action_refine_pills(player: Player) -> str:
    furnace = current_furnace(player)
    success_bonus = int(furnace.get("success_bonus", 0))
    pill_bonus = int(furnace.get("pill_bonus", 0))
    heart_delta = int(furnace.get("heart_demon_delta", 0))
    exposure_delta = int(furnace.get("exposure_delta", 0))
    furnace_text = f"当前丹炉：{furnace.get('name', '无专用丹炉')}。"

    if player.herbs >= 4 and player.spirit_stones >= 2:
        player.herbs -= 4
        player.spirit_stones -= 2
        fail_chance = max(5, 15 - success_bonus // 2)
        fail_roll = random.randint(1, 100)
        if fail_roll <= fail_chance:
            heart_gain = max(1, 2 + heart_delta)
            exposure_gain = max(0, 3 + exposure_delta)
            player.heart_demon += heart_gain
            player.exposure += exposure_gain
            player.hp -= 5
            player.clamp()
            severe = fail_roll <= max(1, fail_chance // 2)
            return (
                f"{furnace_text}{_furnace_fire_text(furnace)}"
                f"{_alchemy_failure_text(furnace, severe)}消耗普通灵草4株和灵石2枚，"
                f"心魔值+{heart_gain}，暴露度+{exposure_gain}，气血-5。"
            )
        made = _roll(2, 4) + pill_bonus
        heart_gain = max(0, 1 + heart_delta)
        exposure_gain = max(0, 2 + exposure_delta)
        player.pills += made
        player.comprehension += 1
        player.heart_demon += heart_gain
        player.exposure += exposure_gain
        player.hp -= 2
        player.clamp()
        return (
            f"{furnace_text}{_furnace_fire_text(furnace)}"
            f"{_alchemy_success_text(furnace, made, 4 + pill_bonus, heart_gain, exposure_gain)}"
            f"消耗普通灵草4株和灵石2枚，得到丹药{made}枚，气血-2。"
        )

    if player.aged_herbs_10 >= 1 and player.spirit_stones >= 3:
        player.aged_herbs_10 -= 1
        player.spirit_stones -= 3
        fail_chance = max(4, 10 - success_bonus // 3)
        fail_roll = random.randint(1, 100)
        if fail_roll <= fail_chance:
            heart_gain = max(1, 3 + heart_delta)
            exposure_gain = max(0, 4 + exposure_delta)
            player.heart_demon += heart_gain
            player.exposure += exposure_gain
            player.hp -= 7
            player.clamp()
            severe = fail_roll <= max(1, fail_chance // 2)
            return (
                f"{furnace_text}{_furnace_fire_text(furnace)}"
                f"{_alchemy_failure_text(furnace, severe)}十年份灵草药力反冲，经脉灼痛，"
                f"心魔值+{heart_gain}，暴露度+{exposure_gain}，气血-7。"
            )
        made = _roll(3, 5) + pill_bonus
        heart_gain = max(1, 2 + heart_delta)
        exposure_gain = max(0, 4 + exposure_delta)
        player.pills += made
        player.comprehension += 1
        player.heart_demon += heart_gain
        player.exposure += exposure_gain
        player.hp -= 3
        player.clamp()
        return (
            f"{furnace_text}{_furnace_fire_text(furnace)}"
            f"{_alchemy_success_text(furnace, made, 5 + pill_bonus, heart_gain, exposure_gain)}"
            f"你用十年份灵草炼得丹药{made}枚，气血-3。"
        )

    if material_total(player) >= 3 and player.spirit_stones >= 1:
        consumed = consume_alchemy_materials(player, 3)
        player.spirit_stones -= 1
        fail_chance = max(6, 18 - success_bonus // 2)
        fail_roll = random.randint(1, 100)
        if fail_roll <= fail_chance:
            heart_gain = max(1, 2 + heart_delta)
            exposure_gain = max(0, 2 + exposure_delta)
            player.heart_demon += heart_gain
            player.exposure += exposure_gain
            player.hp -= 4
            player.clamp()
            severe = fail_roll <= max(1, fail_chance // 2)
            return (
                f"{furnace_text}{_furnace_fire_text(furnace)}"
                f"{_alchemy_failure_text(furnace, severe)}消耗炼丹材料3份和灵石1枚，"
                f"心魔值+{heart_gain}，暴露度+{exposure_gain}，气血-4。"
            )
        made = _roll(2, 3) + pill_bonus
        heart_gain = max(0, 1 + heart_delta)
        exposure_gain = max(0, 1 + exposure_delta)
        player.pills += made
        player.comprehension += 1 if random.random() < 0.70 else 0
        player.heart_demon += heart_gain
        player.exposure += exposure_gain
        player.hp -= 1
        consumed_text = "、".join(f"{MATERIAL_NAMES.get(key, key)}x{value}" for key, value in consumed.items())
        player.clamp()
        return (
            f"{furnace_text}{_furnace_fire_text(furnace)}"
            f"{_alchemy_success_text(furnace, made, 3 + pill_bonus, heart_gain, exposure_gain)}"
            f"你用灵田药材炼成丹药{made}枚。消耗{consumed_text}和灵石1枚，气血-1。"
        )

    player.contribution += 1
    player.npc_affection["沈若兰"] += 1
    player.clamp()
    return f"{furnace_text}材料不足，你改去丹房外围帮忙分拣药材，家族贡献+1，沈若兰好感+1。"


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


def action_status(player: Player) -> str:
    return player.status_text()


def preparation_status_text(player: Player) -> str:
    return "\n\n".join(
        [
            field_status_text(player),
            furnace_status_text(player),
            equipment_status_text(player),
        ]
    )


def _manage_spirit_field(player: Player) -> str:
    print("管理灵田：")
    print("1. 查看灵田")
    print("2. 一键种植")
    print("3. 一键照料")
    print("4. 一键收获")
    print("5. 升级灵田")
    print("6. 购买基础种子包")
    print("0. 返回")
    choice = _read_choice("请选择灵田操作：")

    if choice == "1":
        return field_status_text(player)
    if choice == "2":
        return one_click_plant(player)
    if choice == "3":
        return tend_all_fields(player)
    if choice == "4":
        return harvest_all_fields(player)
    if choice == "5":
        return upgrade_spirit_field(player)
    if choice == "6":
        return buy_seed_pack(player)
    return "你暂时没有处理灵田。"


def _manage_furnace(player: Player) -> str:
    print(furnace_status_text(player))
    print(furnace_shop_text(player))
    selected = _read_choice("请选择炼丹炉：")
    return buy_furnace(player, int(selected)) if selected.isdigit() else "你没有更换炼丹炉。"


def _manage_equipment(player: Player) -> str:
    print("查看/更换装备：")
    print("1. 查看当前装备")
    print("2. 购买轻量装备")
    print("3. 装备/替换装备")
    print("0. 返回")
    choice = _read_choice("请选择装备操作：")

    if choice == "1":
        return equipment_status_text(player)
    if choice == "2":
        print(equipment_shop_text())
        selected = _read_choice("请选择购买装备：")
        return buy_equipment(player, int(selected)) if selected.isdigit() else "你没有购买装备。"
    if choice == "3":
        print(equipment_inventory_text(player))
        selected = _read_choice("请选择装备编号：")
        return equip_item(player, int(selected)) if selected.isdigit() else "你没有更换装备。"
    return "你没有更换装备。"


def action_preparation(player: Player) -> str:
    print("修炼准备：")
    print("1. 管理灵田")
    print("2. 查看/更换炼丹炉")
    print("3. 查看/更换装备")
    print("4. 查看当前准备状态")
    print("0. 返回")
    choice = _read_choice("请选择准备事项：")

    if choice == "1":
        return _manage_spirit_field(player)
    if choice == "2":
        return _manage_furnace(player)
    if choice == "3":
        return _manage_equipment(player)
    if choice == "4":
        return preparation_status_text(player)
    return "你暂时没有做额外准备。"


ACTION_HANDLERS: Dict[str, Callable[[Player], str]] = {
    "1": action_cultivate,
    "2": action_gather_herbs,
    "3": action_refine_pills,
    "4": action_market,
    "5": action_visit_npc,
    "6": action_soul_banner,
    "7": action_status,
    "8": action_preparation,
    "legacy_spirit_field": action_spirit_field,
    "legacy_family_work": action_family_work,
    "legacy_spell_training": action_spell_training,
    "legacy_investigate": action_investigate,
    "legacy_romance": action_romance,
    "legacy_meditate": action_meditate,
}
NON_ADVANCING_ACTIONS = {"7"}


def perform_action(player: Player, choice: str) -> str:
    handler = ACTION_HANDLERS.get(choice)
    if handler is None:
        return "无效行动。"
    result = handler(player)
    if choice not in NON_ADVANCING_ACTIONS:
        player.advance_action()
    return result


def monthly_event(player: Player) -> str:
    player.aged_herbs_sold_this_month = 0
    event = random.choice(MONTHLY_EVENTS)
    for attr, value in event["effects"].items():
        setattr(player, attr, getattr(player, attr) + int(value))
    heishui_text = resolve_monthly_risk_event(player)
    field_text = advance_spirit_fields(player)
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
    if field_text:
        lines.append(field_text)
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
