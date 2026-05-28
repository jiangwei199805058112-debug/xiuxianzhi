"""玩家数据与创建逻辑。"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any, Dict, List

from cultivation_assets import (
    EQUIPMENT_SLOTS,
    EQUIPMENT_ATTR_NAMES,
    current_furnace,
    empty_field,
    equipment_count,
    equipment_effects,
    equipment_score,
    ensure_equipment,
    ensure_spirit_fields,
    grant_starter_seeds,
)
from data import ACTIONS_PER_MONTH, INITIAL_NPC_AFFECTION, NPCS, SPIRIT_ROOTS, TOTAL_ACTIONS
from growth_system import calculate_breadth, mastery_total
from chapter1_event_state import ensure_event_state


MAX_REALM_LEVEL = 9


def _weighted_random_root() -> Dict[str, Any]:
    total_weight = sum(root["weight"] for root in SPIRIT_ROOTS)
    roll = random.randint(1, total_weight)
    cursor = 0
    for root in SPIRIT_ROOTS:
        cursor += root["weight"]
        if roll <= cursor:
            return root
    return SPIRIT_ROOTS[0]


def _int_from(data: Dict[str, Any], key: str, default: int) -> int:
    try:
        return int(data.get(key, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Player:
    name: str
    spirit_root: str
    spirit_root_desc: str
    root_growth: int
    age: int = 16
    realm_level: int = 1
    cultivation_progress: int = 0
    cultivation: int = 5
    physique: int = 5
    comprehension: int = 5
    combat_exp: int = 3
    hp: int = 40
    max_hp: int = 40
    mp: int = 25
    attack: int = 8
    defense: int = 6
    speed: int = 6
    cultivation_speed: int = 5
    divine_sense: int = 3
    luck: int = 1
    charm: int = 1
    dao_heart: int = 5
    intelligence: int = 0
    talisman_guard: int = 0
    talisman_fire: int = 0
    talisman_avoid_fire: int = 0
    talisman_break_armor: int = 0
    black_market_clue: int = 0
    herbs: int = 3
    aged_herbs_10: int = 0
    aged_herbs_30: int = 0
    spirit_stones: int = 5
    pills: int = 1
    contribution: int = 0
    exposure: int = 0
    heart_demon: int = 0
    demonic_qi: int = 0
    karma: int = 0
    righteous_reputation: int = 0
    reputation: int = 0
    enemy_count: int = 0
    foundation: int = 0
    cultivation_mastery: int = 0
    combat_mastery: int = 0
    alchemy_mastery: int = 0
    herb_mastery: int = 0
    spirit_field_mastery: int = 0
    intel_mastery: int = 0
    social_mastery: int = 0
    theft_mastery: int = 0
    demonic_mastery: int = 0
    market_mastery: int = 0
    breakthrough_insight_pending: int = 0
    breakthrough_count: int = 0
    unlocked_insights: List[str] = field(default_factory=list)
    foundation_burst_triggered: bool = False
    theft_skill: int = 0
    theft_exp: int = 0
    theft_attempts: int = 0
    theft_successes: int = 0
    theft_failures: int = 0
    theft_compensations: int = 0
    theft_refusals: int = 0
    theft_escape_count: int = 0
    stolen_manual_fragments: int = 0
    stolen_cultivation_count: int = 0
    stolen_luck_count: int = 0
    stolen_opportunity_count: int = 0
    stolen_fate_count: int = 0
    stolen_lifespan_count: int = 0
    stolen_inheritance_count: int = 0
    theft_high_tier_attempts: int = 0
    theft_high_tier_successes: int = 0
    theft_monthly_event_count: int = 0
    theft_exposure_gain: int = 0
    theft_karma_gain: int = 0
    npc_affection: Dict[str, int] = field(default_factory=dict)
    love_lock_level: int = 1
    has_jade_bottle: bool = False
    has_soul_banner: bool = False
    has_black_market_password: bool = False
    black_market_password_month: int = 0
    souls_refined: int = 0
    aged_herbs_sold_this_month: int = 0
    heishui_market_month: int = 0
    heishui_market_stock: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    heishui_market_events: List[str] = field(default_factory=list)
    heishui_market_spent: int = 0
    heishui_purchase_count: int = 0
    heishui_intel_purchase_count: int = 0
    heishui_black_market_purchase_count: int = 0
    heishui_blindbox_purchase_count: int = 0
    heishui_blindbox_net: int = 0
    heishui_black_intro_count: int = 0
    heishui_black_market_bought_this_month: int = 0
    heishui_bloodbag_bought: int = 0
    heishui_bloodbag_bought_this_month: int = 0
    heishui_risk_event_count: int = 0
    heishui_npc_affection: Dict[str, int] = field(default_factory=dict)
    market_inventory: Dict[str, int] = field(default_factory=dict)
    intelligence_log: List[str] = field(default_factory=list)
    market_flags: List[str] = field(default_factory=list)
    consignment_items: List[Dict[str, Any]] = field(default_factory=list)
    explore_intel_bonus: int = 0
    heishui_tournament_bonuses: Dict[str, int] = field(default_factory=dict)
    heishui_price_modifiers: Dict[str, int] = field(default_factory=dict)
    heishui_price_modifier_month: int = 0
    tracking_marks: int = 0
    spirit_fields: List[Dict[str, Any]] = field(default_factory=lambda: [empty_field(1)])
    spirit_field_harvest_count: int = 0
    alchemy_furnace_id: str = "none"
    equipment_inventory: Dict[str, int] = field(default_factory=dict)
    equipped_items: Dict[str, str] = field(default_factory=lambda: {slot: "" for slot in EQUIPMENT_SLOTS})
    tutorial_flags: List[str] = field(default_factory=list)
    total_actions: int = 0
    ending_flags: List[str] = field(default_factory=list)
    triggered_event_ids: List[str] = field(default_factory=list)
    event_cooldowns: Dict[str, int] = field(default_factory=dict)
    monthly_event_log: List[Dict[str, Any]] = field(default_factory=list)
    monthly_action_counts: Dict[str, int] = field(default_factory=dict)
    route_tags: List[str] = field(default_factory=list)
    theft_trace_level: int = 0
    theft_suspicion_level: int = 0
    blackwater_debt: int = 0
    blackwater_trace_level: int = 0
    market_dependency_level: int = 0
    talisman_failure_risk: int = 0
    demonic_contamination: int = 0
    pill_toxin_level: int = 0
    public_scandal_level: int = 0
    field_pollution_level: int = 0
    consumable_dependency_level: int = 0
    resource_scatter_level: int = 0
    orthodox_path_level: int = 0
    farming_path_level: int = 0
    alchemy_path_level: int = 0
    theft_path_level: int = 0
    blackwater_path_level: int = 0
    intel_social_path_level: int = 0
    demonic_path_level: int = 0
    market_talisman_path_level: int = 0
    mixed_path_score: int = 0

    def __post_init__(self) -> None:
        if not self.npc_affection:
            self.npc_affection = dict(INITIAL_NPC_AFFECTION)
        self.clamp()

    @property
    def month(self) -> int:
        return min(12, self.total_actions // ACTIONS_PER_MONTH + 1)

    @property
    def action_in_month(self) -> int:
        return self.total_actions % ACTIONS_PER_MONTH + 1

    @property
    def finished(self) -> bool:
        return self.total_actions >= TOTAL_ACTIONS

    def realm_name(self) -> str:
        return f"炼气{self.realm_level}层"

    def _increase_realm_once(self) -> None:
        self.realm_level += 1
        self.breakthrough_count += 1
        self.breakthrough_insight_pending += 1
        self.max_hp += 8
        self.hp = self.max_hp
        self.mp += 5
        self.attack += 2
        self.defense += 1
        self.speed += 1
        self.divine_sense += 1
        self.cultivation += 5

    def gain_cultivation_progress(self, amount: int) -> None:
        self.cultivation_progress += max(0, amount)
        self.cultivation += max(0, amount) // 3
        self.clamp()

    def clamp(self) -> None:
        ensure_event_state(self)
        numeric_min_zero = [
            "cultivation_progress",
            "cultivation",
            "physique",
            "comprehension",
            "combat_exp",
            "hp",
            "max_hp",
            "mp",
            "attack",
            "defense",
            "speed",
            "cultivation_speed",
            "divine_sense",
            "luck",
            "charm",
            "dao_heart",
            "intelligence",
            "talisman_guard",
            "talisman_fire",
            "talisman_avoid_fire",
            "talisman_break_armor",
            "black_market_clue",
            "herbs",
            "aged_herbs_10",
            "aged_herbs_30",
            "spirit_stones",
            "pills",
            "contribution",
            "exposure",
            "heart_demon",
            "demonic_qi",
            "karma",
            "enemy_count",
            "foundation",
            "cultivation_mastery",
            "combat_mastery",
            "alchemy_mastery",
            "herb_mastery",
            "spirit_field_mastery",
            "intel_mastery",
            "social_mastery",
            "theft_mastery",
            "demonic_mastery",
            "market_mastery",
            "breakthrough_insight_pending",
            "breakthrough_count",
            "theft_skill",
            "theft_exp",
            "theft_attempts",
            "theft_successes",
            "theft_failures",
            "theft_compensations",
            "theft_refusals",
            "theft_escape_count",
            "stolen_manual_fragments",
            "stolen_cultivation_count",
            "stolen_luck_count",
            "stolen_opportunity_count",
            "stolen_fate_count",
            "stolen_lifespan_count",
            "stolen_inheritance_count",
            "theft_high_tier_attempts",
            "theft_high_tier_successes",
            "theft_monthly_event_count",
            "theft_exposure_gain",
            "theft_karma_gain",
            "souls_refined",
            "aged_herbs_sold_this_month",
            "black_market_password_month",
            "heishui_market_month",
            "heishui_market_spent",
            "heishui_purchase_count",
            "heishui_intel_purchase_count",
            "heishui_black_market_purchase_count",
            "heishui_blindbox_purchase_count",
            "heishui_black_intro_count",
            "heishui_black_market_bought_this_month",
            "heishui_bloodbag_bought",
            "heishui_bloodbag_bought_this_month",
            "heishui_risk_event_count",
            "explore_intel_bonus",
            "heishui_price_modifier_month",
            "tracking_marks",
            "spirit_field_harvest_count",
            "total_actions",
            "theft_trace_level",
            "theft_suspicion_level",
            "blackwater_debt",
            "blackwater_trace_level",
            "market_dependency_level",
            "talisman_failure_risk",
            "demonic_contamination",
            "pill_toxin_level",
            "public_scandal_level",
            "field_pollution_level",
            "consumable_dependency_level",
            "resource_scatter_level",
            "orthodox_path_level",
            "farming_path_level",
            "alchemy_path_level",
            "theft_path_level",
            "blackwater_path_level",
            "intel_social_path_level",
            "demonic_path_level",
            "market_talisman_path_level",
            "mixed_path_score",
        ]
        for attr in numeric_min_zero:
            if getattr(self, attr) < 0:
                setattr(self, attr, 0)

        self.age = max(1, self.age)
        self.realm_level = max(1, min(self.realm_level, MAX_REALM_LEVEL))
        while self.cultivation_progress >= 100 and self.realm_level < MAX_REALM_LEVEL:
            self.cultivation_progress -= 100
            self._increase_realm_once()
        if self.realm_level >= MAX_REALM_LEVEL:
            self.cultivation_progress = min(self.cultivation_progress, 99)

        self.max_hp = max(1, self.max_hp)
        self.hp = max(0, min(self.hp, self.max_hp))
        self.exposure = min(self.exposure, 100)
        self.heart_demon = min(self.heart_demon, 100)
        self.demonic_qi = min(self.demonic_qi, 100)
        self.karma = min(self.karma, 100)
        for attr in (
            "theft_trace_level",
            "theft_suspicion_level",
            "blackwater_debt",
            "blackwater_trace_level",
            "market_dependency_level",
            "talisman_failure_risk",
            "public_scandal_level",
            "field_pollution_level",
            "consumable_dependency_level",
            "resource_scatter_level",
            "demonic_contamination",
            "pill_toxin_level",
        ):
            setattr(self, attr, min(getattr(self, attr), 100))
        self.righteous_reputation = max(-100, min(self.righteous_reputation, 100))
        self.reputation = max(-100, min(self.reputation, 100))
        self.theft_skill = min(self.theft_skill, 100)
        self.foundation = min(self.foundation, 160)
        for attr in (
            "cultivation_mastery",
            "combat_mastery",
            "alchemy_mastery",
            "herb_mastery",
            "spirit_field_mastery",
            "intel_mastery",
            "social_mastery",
            "theft_mastery",
            "demonic_mastery",
            "market_mastery",
        ):
            setattr(self, attr, min(getattr(self, attr), 160))
        self.unlocked_insights = [str(name) for name in self.unlocked_insights if str(name)]
        self.total_actions = max(0, min(self.total_actions, TOTAL_ACTIONS))
        if self.black_market_password_month != self.month:
            self.has_black_market_password = False

        cleaned_affection: Dict[str, int] = {}
        for npc in NPCS:
            value = self.npc_affection.get(npc, INITIAL_NPC_AFFECTION[npc])
            try:
                affection = int(value)
            except (TypeError, ValueError):
                affection = INITIAL_NPC_AFFECTION[npc]
            cleaned_affection[npc] = max(-100, min(affection, 100))
        self.npc_affection = cleaned_affection

        for key, value in list(self.heishui_npc_affection.items()):
            try:
                relation = int(value)
            except (TypeError, ValueError):
                relation = 0
            self.heishui_npc_affection[str(key)] = max(-100, min(relation, 100))

        for key, value in list(self.market_inventory.items()):
            try:
                count = int(value)
            except (TypeError, ValueError):
                count = 0
            if count <= 0:
                del self.market_inventory[key]
            else:
                self.market_inventory[str(key)] = count

        for mapping_name in ("heishui_tournament_bonuses", "heishui_price_modifiers"):
            mapping = getattr(self, mapping_name)
            for key, value in list(mapping.items()):
                try:
                    mapping[str(key)] = int(value)
                except (TypeError, ValueError):
                    del mapping[key]

        if self.heishui_price_modifier_month and self.heishui_price_modifier_month < self.month:
            self.heishui_price_modifiers = {}

        ensure_spirit_fields(self)
        ensure_equipment(self)
        self.tutorial_flags = [str(flag) for flag in self.tutorial_flags if str(flag)]
        ensure_event_state(self)

    def advance_action(self) -> None:
        self.total_actions += 1
        self.clamp()

    def average_affection(self) -> float:
        if not self.npc_affection:
            return 0.0
        return sum(self.npc_affection.values()) / len(self.npc_affection)

    def status_text(self) -> str:
        affection_text = "，".join(f"{name}{value:+d}" for name, value in self.npc_affection.items())
        jade_text = "已得" if self.has_jade_bottle else "未得"
        banner_text = "已得" if self.has_soul_banner else "未得"
        furnace = current_furnace(self)
        equipment_effect_text = "、".join(
            f"{EQUIPMENT_ATTR_NAMES[key]}{value:+d}"
            for key, value in equipment_effects(self).items()
            if value
        )
        if not equipment_effect_text:
            equipment_effect_text = "无"
        mastery_text = (
            f"修炼{self.cultivation_mastery}｜斗法{self.combat_mastery}｜炼丹{self.alchemy_mastery}｜"
            f"采药{self.herb_mastery}｜灵植{self.spirit_field_mastery}｜情报{self.intel_mastery}｜"
            f"人情{self.social_mastery}｜盗术{self.theft_mastery}｜魔道{self.demonic_mastery}｜坊市{self.market_mastery}"
        )
        insight_text = "、".join(self.unlocked_insights) if self.unlocked_insights else "无"
        return (
            f"姓名：{self.name}｜年龄：{self.age}\n"
            f"出身：青岭沈家旁支\n"
            f"灵根：{self.spirit_root}（{self.spirit_root_desc}）\n"
            f"境界：{self.realm_name()}｜修炼进度{self.cultivation_progress}/100｜修为{self.cultivation}\n"
            f"战力：气血{self.hp}/{self.max_hp}｜灵力{self.mp}｜攻击{self.attack}｜防御{self.defense}｜身法{self.speed}\n"
            f"资质：体魄{self.physique}｜悟性{self.comprehension}｜斗法经验{self.combat_exp}｜修炼速度{self.cultivation_speed}\n"
            f"心性：神识{self.divine_sense}｜气运{self.luck}｜魅力{self.charm}｜道心{self.dao_heart}｜情报值{self.intelligence}\n"
            f"符箓：护身符{self.talisman_guard}｜火弹符{self.talisman_fire}｜避火符{self.talisman_avoid_fire}｜破甲符{self.talisman_break_armor}｜黑市线索{self.black_market_clue}\n"
            f"资源：普通灵草{self.herbs}｜十年份灵草{self.aged_herbs_10}｜三十年份灵草{self.aged_herbs_30}｜灵石{self.spirit_stones}｜丹药{self.pills}｜家族贡献{self.contribution}\n"
            f"经营：灵田{len(self.spirit_fields)}块｜灵田收获{self.spirit_field_harvest_count}次｜丹炉{furnace.get('name', '无专用丹炉')}\n"
            f"装备：持有{equipment_count(self)}件｜评分{equipment_score(self)}｜加成{equipment_effect_text}\n"
            f"根基：根基{self.foundation}｜博学度{calculate_breadth(self)}｜熟练总和{mastery_total(self)}｜突破{self.breakthrough_count}次｜待选感悟{self.breakthrough_insight_pending}\n"
            f"熟练：{mastery_text}\n"
            f"融会：{len(self.unlocked_insights)}项｜{insight_text}｜厚积薄发{'已触发' if self.foundation_burst_triggered else '未触发'}\n"
            f"隐患：暴露度{self.exposure}｜心魔值{self.heart_demon}｜魔气值{self.demonic_qi}｜业力值{self.karma}\n"
            f"名声：正道声望{self.righteous_reputation}｜旁门声望{self.reputation:+d}｜结仇{self.enemy_count}\n"
            f"盗术：等级{self.theft_skill}｜经验{self.theft_exp}｜尝试{self.theft_attempts}｜成功{self.theft_successes}｜失败{self.theft_failures}｜赔偿{self.theft_compensations}｜拒赔{self.theft_refusals}｜强逃{self.theft_escape_count}\n"
            f"盗术高阶：高阶尝试{self.theft_high_tier_attempts}｜高阶成功{self.theft_high_tier_successes}｜功法残页{self.stolen_manual_fragments}｜偷修为{self.stolen_cultivation_count}｜偷气运{self.stolen_luck_count}｜偷机缘{self.stolen_opportunity_count}｜偷因果{self.stolen_fate_count}｜偷寿元{self.stolen_lifespan_count}｜偷传承{self.stolen_inheritance_count}｜月末反噬{self.theft_monthly_event_count}\n"
            f"族人好感：{affection_text}\n"
            f"隐藏：古玉瓶{jade_text}｜残破魂幡{banner_text}｜黑市暗号{'已持有' if self.has_black_market_password else '未持有'}｜追踪标记{self.tracking_marks}｜情意锁低阶｜炼魂次数{self.souls_refined}"
        )

    def to_dict(self) -> Dict[str, Any]:
        self.clamp()
        return {
            "name": self.name,
            "spirit_root": self.spirit_root,
            "spirit_root_desc": self.spirit_root_desc,
            "root_growth": self.root_growth,
            "age": self.age,
            "realm_level": self.realm_level,
            "cultivation_progress": self.cultivation_progress,
            "cultivation": self.cultivation,
            "physique": self.physique,
            "comprehension": self.comprehension,
            "combat_exp": self.combat_exp,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "cultivation_speed": self.cultivation_speed,
            "divine_sense": self.divine_sense,
            "luck": self.luck,
            "charm": self.charm,
            "dao_heart": self.dao_heart,
            "intelligence": self.intelligence,
            "talisman_guard": self.talisman_guard,
            "talisman_fire": self.talisman_fire,
            "talisman_avoid_fire": self.talisman_avoid_fire,
            "talisman_break_armor": self.talisman_break_armor,
            "black_market_clue": self.black_market_clue,
            "herbs": self.herbs,
            "aged_herbs_10": self.aged_herbs_10,
            "aged_herbs_30": self.aged_herbs_30,
            "spirit_stones": self.spirit_stones,
            "pills": self.pills,
            "contribution": self.contribution,
            "exposure": self.exposure,
            "heart_demon": self.heart_demon,
            "demonic_qi": self.demonic_qi,
            "karma": self.karma,
            "righteous_reputation": self.righteous_reputation,
            "reputation": self.reputation,
            "enemy_count": self.enemy_count,
            "foundation": self.foundation,
            "cultivation_mastery": self.cultivation_mastery,
            "combat_mastery": self.combat_mastery,
            "alchemy_mastery": self.alchemy_mastery,
            "herb_mastery": self.herb_mastery,
            "spirit_field_mastery": self.spirit_field_mastery,
            "intel_mastery": self.intel_mastery,
            "social_mastery": self.social_mastery,
            "theft_mastery": self.theft_mastery,
            "demonic_mastery": self.demonic_mastery,
            "market_mastery": self.market_mastery,
            "breakthrough_insight_pending": self.breakthrough_insight_pending,
            "breakthrough_count": self.breakthrough_count,
            "unlocked_insights": self.unlocked_insights,
            "foundation_burst_triggered": self.foundation_burst_triggered,
            "theft_skill": self.theft_skill,
            "theft_exp": self.theft_exp,
            "theft_attempts": self.theft_attempts,
            "theft_successes": self.theft_successes,
            "theft_failures": self.theft_failures,
            "theft_compensations": self.theft_compensations,
            "theft_refusals": self.theft_refusals,
            "theft_escape_count": self.theft_escape_count,
            "stolen_manual_fragments": self.stolen_manual_fragments,
            "stolen_cultivation_count": self.stolen_cultivation_count,
            "stolen_luck_count": self.stolen_luck_count,
            "stolen_opportunity_count": self.stolen_opportunity_count,
            "stolen_fate_count": self.stolen_fate_count,
            "stolen_lifespan_count": self.stolen_lifespan_count,
            "stolen_inheritance_count": self.stolen_inheritance_count,
            "theft_high_tier_attempts": self.theft_high_tier_attempts,
            "theft_high_tier_successes": self.theft_high_tier_successes,
            "theft_monthly_event_count": self.theft_monthly_event_count,
            "theft_exposure_gain": self.theft_exposure_gain,
            "theft_karma_gain": self.theft_karma_gain,
            "npc_affection": self.npc_affection,
            "love_lock_level": self.love_lock_level,
            "has_jade_bottle": self.has_jade_bottle,
            "has_soul_banner": self.has_soul_banner,
            "has_black_market_password": self.has_black_market_password,
            "black_market_password_month": self.black_market_password_month,
            "souls_refined": self.souls_refined,
            "aged_herbs_sold_this_month": self.aged_herbs_sold_this_month,
            "heishui_market_month": self.heishui_market_month,
            "heishui_market_stock": self.heishui_market_stock,
            "heishui_market_events": self.heishui_market_events,
            "heishui_market_spent": self.heishui_market_spent,
            "heishui_purchase_count": self.heishui_purchase_count,
            "heishui_intel_purchase_count": self.heishui_intel_purchase_count,
            "heishui_black_market_purchase_count": self.heishui_black_market_purchase_count,
            "heishui_blindbox_purchase_count": self.heishui_blindbox_purchase_count,
            "heishui_blindbox_net": self.heishui_blindbox_net,
            "heishui_black_intro_count": self.heishui_black_intro_count,
            "heishui_black_market_bought_this_month": self.heishui_black_market_bought_this_month,
            "heishui_bloodbag_bought": self.heishui_bloodbag_bought,
            "heishui_bloodbag_bought_this_month": self.heishui_bloodbag_bought_this_month,
            "heishui_risk_event_count": self.heishui_risk_event_count,
            "heishui_npc_affection": self.heishui_npc_affection,
            "market_inventory": self.market_inventory,
            "intelligence_log": self.intelligence_log,
            "market_flags": self.market_flags,
            "consignment_items": self.consignment_items,
            "explore_intel_bonus": self.explore_intel_bonus,
            "heishui_tournament_bonuses": self.heishui_tournament_bonuses,
            "heishui_price_modifiers": self.heishui_price_modifiers,
            "heishui_price_modifier_month": self.heishui_price_modifier_month,
            "tracking_marks": self.tracking_marks,
            "spirit_fields": self.spirit_fields,
            "spirit_field_harvest_count": self.spirit_field_harvest_count,
            "alchemy_furnace_id": self.alchemy_furnace_id,
            "equipment_inventory": self.equipment_inventory,
            "equipped_items": self.equipped_items,
            "tutorial_flags": self.tutorial_flags,
            "total_actions": self.total_actions,
            "ending_flags": self.ending_flags,
            "triggered_event_ids": self.triggered_event_ids,
            "event_cooldowns": self.event_cooldowns,
            "monthly_event_log": self.monthly_event_log,
            "monthly_action_counts": self.monthly_action_counts,
            "route_tags": self.route_tags,
            "theft_trace_level": self.theft_trace_level,
            "theft_suspicion_level": self.theft_suspicion_level,
            "blackwater_debt": self.blackwater_debt,
            "blackwater_trace_level": self.blackwater_trace_level,
            "market_dependency_level": self.market_dependency_level,
            "talisman_failure_risk": self.talisman_failure_risk,
            "demonic_contamination": self.demonic_contamination,
            "pill_toxin_level": self.pill_toxin_level,
            "public_scandal_level": self.public_scandal_level,
            "field_pollution_level": self.field_pollution_level,
            "consumable_dependency_level": self.consumable_dependency_level,
            "resource_scatter_level": self.resource_scatter_level,
            "orthodox_path_level": self.orthodox_path_level,
            "farming_path_level": self.farming_path_level,
            "alchemy_path_level": self.alchemy_path_level,
            "theft_path_level": self.theft_path_level,
            "blackwater_path_level": self.blackwater_path_level,
            "intel_social_path_level": self.intel_social_path_level,
            "demonic_path_level": self.demonic_path_level,
            "market_talisman_path_level": self.market_talisman_path_level,
            "mixed_path_score": self.mixed_path_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        old_cultivation = _int_from(data, "cultivation", 5)
        inferred_realm = max(1, min(MAX_REALM_LEVEL, old_cultivation // 40 + 1))
        realm_level = _int_from(data, "realm_level", inferred_realm)
        max_hp = _int_from(data, "max_hp", 40 + max(0, realm_level - 1) * 8)
        combat_exp = _int_from(data, "combat_exp", 3)
        player = cls(
            name=str(data.get("name", "沈无名")),
            spirit_root=str(data.get("spirit_root", "五行杂灵根")),
            spirit_root_desc=str(data.get("spirit_root_desc", "旧存档未记录灵根说明。")),
            root_growth=_int_from(data, "root_growth", 0),
            age=_int_from(data, "age", 16),
            realm_level=realm_level,
            cultivation_progress=_int_from(data, "cultivation_progress", 0),
            cultivation=old_cultivation,
            physique=_int_from(data, "physique", 5),
            comprehension=_int_from(data, "comprehension", 5),
            combat_exp=combat_exp,
            hp=_int_from(data, "hp", max_hp),
            max_hp=max_hp,
            mp=_int_from(data, "mp", 25 + max(0, realm_level - 1) * 5),
            attack=_int_from(data, "attack", 8 + combat_exp // 2 + max(0, realm_level - 1) * 2),
            defense=_int_from(data, "defense", 6 + max(0, realm_level - 1)),
            speed=_int_from(data, "speed", 6 + max(0, realm_level - 1)),
            cultivation_speed=_int_from(data, "cultivation_speed", 5 + _int_from(data, "root_growth", 0)),
            divine_sense=_int_from(data, "divine_sense", 3 + max(0, realm_level - 1)),
            luck=_int_from(data, "luck", 1),
            charm=_int_from(data, "charm", 1),
            dao_heart=_int_from(data, "dao_heart", 5),
            intelligence=_int_from(data, "intelligence", 0),
            talisman_guard=_int_from(data, "talisman_guard", 0),
            talisman_fire=_int_from(data, "talisman_fire", 0),
            talisman_avoid_fire=_int_from(data, "talisman_avoid_fire", 0),
            talisman_break_armor=_int_from(data, "talisman_break_armor", 0),
            black_market_clue=_int_from(data, "black_market_clue", 0),
            herbs=_int_from(data, "herbs", 3),
            aged_herbs_10=_int_from(data, "aged_herbs_10", 0),
            aged_herbs_30=_int_from(data, "aged_herbs_30", 0),
            spirit_stones=_int_from(data, "spirit_stones", 5),
            pills=_int_from(data, "pills", 1),
            contribution=_int_from(data, "contribution", 0),
            exposure=_int_from(data, "exposure", 0),
            heart_demon=_int_from(data, "heart_demon", 0),
            demonic_qi=_int_from(data, "demonic_qi", 0),
            karma=_int_from(data, "karma", 0),
            righteous_reputation=_int_from(data, "righteous_reputation", 0),
            reputation=_int_from(data, "reputation", 0),
            enemy_count=_int_from(data, "enemy_count", _int_from(data, "grudges", 0)),
            foundation=_int_from(data, "foundation", 0),
            cultivation_mastery=_int_from(data, "cultivation_mastery", 0),
            combat_mastery=_int_from(data, "combat_mastery", 0),
            alchemy_mastery=_int_from(data, "alchemy_mastery", 0),
            herb_mastery=_int_from(data, "herb_mastery", 0),
            spirit_field_mastery=_int_from(data, "spirit_field_mastery", 0),
            intel_mastery=_int_from(data, "intel_mastery", 0),
            social_mastery=_int_from(data, "social_mastery", 0),
            theft_mastery=_int_from(data, "theft_mastery", 0),
            demonic_mastery=_int_from(data, "demonic_mastery", 0),
            market_mastery=_int_from(data, "market_mastery", 0),
            breakthrough_insight_pending=_int_from(data, "breakthrough_insight_pending", 0),
            breakthrough_count=_int_from(data, "breakthrough_count", 0),
            unlocked_insights=list(data.get("unlocked_insights") or []),
            foundation_burst_triggered=bool(data.get("foundation_burst_triggered", False)),
            theft_skill=_int_from(data, "theft_skill", 0),
            theft_exp=_int_from(data, "theft_exp", 0),
            theft_attempts=_int_from(data, "theft_attempts", 0),
            theft_successes=_int_from(data, "theft_successes", 0),
            theft_failures=_int_from(data, "theft_failures", 0),
            theft_compensations=_int_from(data, "theft_compensations", 0),
            theft_refusals=_int_from(data, "theft_refusals", 0),
            theft_escape_count=_int_from(data, "theft_escape_count", 0),
            stolen_manual_fragments=_int_from(data, "stolen_manual_fragments", 0),
            stolen_cultivation_count=_int_from(data, "stolen_cultivation_count", 0),
            stolen_luck_count=_int_from(data, "stolen_luck_count", 0),
            stolen_opportunity_count=_int_from(data, "stolen_opportunity_count", _int_from(data, "stolen_chance_count", 0)),
            stolen_fate_count=_int_from(data, "stolen_fate_count", 0),
            stolen_lifespan_count=_int_from(data, "stolen_lifespan_count", 0),
            stolen_inheritance_count=_int_from(data, "stolen_inheritance_count", 0),
            theft_high_tier_attempts=_int_from(data, "theft_high_tier_attempts", 0),
            theft_high_tier_successes=_int_from(data, "theft_high_tier_successes", 0),
            theft_monthly_event_count=_int_from(data, "theft_monthly_event_count", 0),
            theft_exposure_gain=_int_from(data, "theft_exposure_gain", 0),
            theft_karma_gain=_int_from(data, "theft_karma_gain", 0),
            npc_affection=dict(data.get("npc_affection") or {}),
            love_lock_level=_int_from(data, "love_lock_level", 1),
            has_jade_bottle=bool(data.get("has_jade_bottle", False)),
            has_soul_banner=bool(data.get("has_soul_banner", data.get("soul_banner_awakened", False))),
            has_black_market_password=bool(data.get("has_black_market_password", False)),
            black_market_password_month=_int_from(data, "black_market_password_month", 0),
            souls_refined=_int_from(data, "souls_refined", 0),
            aged_herbs_sold_this_month=_int_from(data, "aged_herbs_sold_this_month", 0),
            heishui_market_month=_int_from(data, "heishui_market_month", 0),
            heishui_market_stock=dict(data.get("heishui_market_stock") or {}),
            heishui_market_events=list(data.get("heishui_market_events") or []),
            heishui_market_spent=_int_from(data, "heishui_market_spent", 0),
            heishui_purchase_count=_int_from(data, "heishui_purchase_count", 0),
            heishui_intel_purchase_count=_int_from(data, "heishui_intel_purchase_count", 0),
            heishui_black_market_purchase_count=_int_from(data, "heishui_black_market_purchase_count", 0),
            heishui_blindbox_purchase_count=_int_from(data, "heishui_blindbox_purchase_count", 0),
            heishui_blindbox_net=_int_from(data, "heishui_blindbox_net", 0),
            heishui_black_intro_count=_int_from(data, "heishui_black_intro_count", 0),
            heishui_black_market_bought_this_month=_int_from(data, "heishui_black_market_bought_this_month", 0),
            heishui_bloodbag_bought=_int_from(data, "heishui_bloodbag_bought", 0),
            heishui_bloodbag_bought_this_month=_int_from(data, "heishui_bloodbag_bought_this_month", 0),
            heishui_risk_event_count=_int_from(data, "heishui_risk_event_count", 0),
            heishui_npc_affection=dict(data.get("heishui_npc_affection") or {}),
            market_inventory=dict(data.get("market_inventory") or {}),
            intelligence_log=list(data.get("intelligence_log") or []),
            market_flags=list(data.get("market_flags") or []),
            consignment_items=list(data.get("consignment_items") or []),
            explore_intel_bonus=_int_from(data, "explore_intel_bonus", 0),
            heishui_tournament_bonuses=dict(data.get("heishui_tournament_bonuses") or {}),
            heishui_price_modifiers=dict(data.get("heishui_price_modifiers") or {}),
            heishui_price_modifier_month=_int_from(data, "heishui_price_modifier_month", 0),
            tracking_marks=_int_from(data, "tracking_marks", 0),
            spirit_fields=list(data.get("spirit_fields") or [empty_field(1)]),
            spirit_field_harvest_count=_int_from(data, "spirit_field_harvest_count", 0),
            alchemy_furnace_id=str(data.get("alchemy_furnace_id", "none") or "none"),
            equipment_inventory=dict(data.get("equipment_inventory") or {}),
            equipped_items=dict(data.get("equipped_items") or {}),
            tutorial_flags=list(data.get("tutorial_flags") or []),
            total_actions=_int_from(data, "total_actions", 0),
            ending_flags=list(data.get("ending_flags", [])),
            triggered_event_ids=list(data.get("triggered_event_ids") or []),
            event_cooldowns=dict(data.get("event_cooldowns") or {}),
            monthly_event_log=list(data.get("monthly_event_log") or []),
            monthly_action_counts=dict(data.get("monthly_action_counts") or {}),
            route_tags=list(data.get("route_tags") or []),
            theft_trace_level=_int_from(data, "theft_trace_level", 0),
            theft_suspicion_level=_int_from(data, "theft_suspicion_level", 0),
            blackwater_debt=_int_from(data, "blackwater_debt", 0),
            blackwater_trace_level=_int_from(data, "blackwater_trace_level", 0),
            market_dependency_level=_int_from(data, "market_dependency_level", _int_from(data, "consumable_dependency_level", 0)),
            talisman_failure_risk=_int_from(data, "talisman_failure_risk", 0),
            demonic_contamination=_int_from(data, "demonic_contamination", 0),
            pill_toxin_level=_int_from(data, "pill_toxin_level", 0),
            public_scandal_level=_int_from(data, "public_scandal_level", 0),
            field_pollution_level=_int_from(data, "field_pollution_level", 0),
            consumable_dependency_level=_int_from(data, "consumable_dependency_level", 0),
            resource_scatter_level=_int_from(data, "resource_scatter_level", 0),
            orthodox_path_level=_int_from(data, "orthodox_path_level", 0),
            farming_path_level=_int_from(data, "farming_path_level", 0),
            alchemy_path_level=_int_from(data, "alchemy_path_level", 0),
            theft_path_level=_int_from(data, "theft_path_level", 0),
            blackwater_path_level=_int_from(data, "blackwater_path_level", 0),
            intel_social_path_level=_int_from(data, "intel_social_path_level", 0),
            demonic_path_level=_int_from(data, "demonic_path_level", 0),
            market_talisman_path_level=_int_from(data, "market_talisman_path_level", 0),
            mixed_path_score=_int_from(data, "mixed_path_score", 0),
        )
        player.clamp()
        return player


def create_player(name: str) -> Player:
    clean_name = name.strip() or "沈无名"
    root = _weighted_random_root()
    player = Player(
        name=clean_name,
        spirit_root=root["name"],
        spirit_root_desc=root["desc"],
        root_growth=int(root["growth"]),
    )
    for attr, value in root["modifiers"].items():
        setattr(player, attr, getattr(player, attr) + int(value))
    player.hp = player.max_hp
    grant_starter_seeds(player)
    player.clamp()
    return player
