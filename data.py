"""第一章《旁支入道》的静态数据。"""

VERSION = "v0.1.10"
HEISHUI_MARKET_VERSION = "v1.1"
CHAPTER_NAME = "旁支入道"
FAMILY_NAME = "青岭沈家"
TOTAL_MONTHS = 12
ACTIONS_PER_MONTH = 3
TOTAL_ACTIONS = TOTAL_MONTHS * ACTIONS_PER_MONTH

SPIRIT_ROOTS = [
    {
        "name": "五行杂灵根",
        "weight": 34,
        "desc": "五行皆沾，进境缓慢，却胜在根基宽厚。",
        "modifiers": {
            "cultivation": 0,
            "physique": 1,
            "comprehension": 1,
            "combat_exp": 0,
            "cultivation_speed": 0,
            "dao_heart": 1,
        },
        "growth": 0,
    },
    {
        "name": "四灵根",
        "weight": 28,
        "desc": "旁支常见资质，只要肯熬，也能在族中站稳脚跟。",
        "modifiers": {
            "cultivation": 1,
            "physique": 1,
            "comprehension": 1,
            "combat_exp": 0,
            "cultivation_speed": 1,
        },
        "growth": 1,
    },
    {
        "name": "三灵根",
        "weight": 22,
        "desc": "修炼较顺，若有资源扶持，足以争一争大比名次。",
        "modifiers": {
            "cultivation": 2,
            "physique": 0,
            "comprehension": 1,
            "combat_exp": 1,
            "cultivation_speed": 2,
            "divine_sense": 1,
        },
        "growth": 2,
    },
    {
        "name": "双灵根",
        "weight": 12,
        "desc": "资质不俗，即便出身旁支，也会被族老多看一眼。",
        "modifiers": {
            "cultivation": 3,
            "physique": 0,
            "comprehension": 2,
            "combat_exp": 1,
            "cultivation_speed": 3,
            "divine_sense": 2,
            "charm": 1,
        },
        "growth": 3,
    },
    {
        "name": "异灵根",
        "weight": 4,
        "desc": "灵机偏锋，悟性出众，但也容易惹来审视。",
        "modifiers": {
            "cultivation": 2,
            "physique": 0,
            "comprehension": 3,
            "combat_exp": 2,
            "cultivation_speed": 3,
            "divine_sense": 3,
            "luck": 1,
        },
        "growth": 3,
    },
]

NPCS = {
    "沈若兰": "药田一脉的旁支少女，心细，重视踏实做事。",
    "沈云庭": "青岭沈家直系天才，眼高于顶，是大比前十热门。",
    "沈子岳": "爽朗的同辈子弟，常在演武场与人切磋。",
    "沈怀安": "族中杂务管事，记性很好，也记仇。",
    "沈霜": "冷淡少言的族中少女，常替族老整理情报。",
    "沈墨阳": "阴沉的直系子弟，对旁支向来轻慢。",
}

INITIAL_NPC_AFFECTION = {
    "沈若兰": 0,
    "沈云庭": -10,
    "沈子岳": 0,
    "沈怀安": -5,
    "沈霜": 0,
    "沈墨阳": -20,
}

MONTH_NAMES = [
    "正月",
    "二月",
    "三月",
    "四月",
    "五月",
    "六月",
    "七月",
    "八月",
    "九月",
    "十月",
    "冬月",
    "腊月",
]

ACTION_NAMES = {
    "1": "打坐修炼",
    "2": "百药山采药",
    "3": "偷偷炼丹",
    "4": "坊市交易",
    "5": "结交族人",
    "6": "魔道炼魂",
    "7": "查看状态",
    "8": "修炼准备",
    "9": "存档",
    "0": "退出",
}

ATTRIBUTE_NAMES = {
    "age": "年龄",
    "realm_level": "境界层数",
    "cultivation_progress": "修炼进度",
    "cultivation": "修为",
    "physique": "体魄",
    "comprehension": "悟性",
    "combat_exp": "斗法经验",
    "hp": "气血",
    "max_hp": "气血上限",
    "mp": "灵力",
    "attack": "攻击",
    "defense": "防御",
    "speed": "身法",
    "cultivation_speed": "修炼速度",
    "divine_sense": "神识",
    "luck": "气运",
    "charm": "魅力",
    "dao_heart": "道心",
    "intelligence": "情报值",
    "talisman_guard": "护身符",
    "talisman_fire": "火弹符",
    "talisman_avoid_fire": "避火符",
    "talisman_break_armor": "破甲符",
    "black_market_clue": "黑市线索",
    "herbs": "普通灵草",
    "aged_herbs_10": "十年份灵草",
    "aged_herbs_30": "三十年份灵草",
    "spirit_stones": "灵石",
    "pills": "丹药",
    "contribution": "家族贡献",
    "exposure": "暴露度",
    "heart_demon": "心魔值",
    "demonic_qi": "魔气值",
    "karma": "业力值",
    "righteous_reputation": "正道声望",
}

MARKET_PRICES = {
    "普通灵草": 2,
    "十年份灵草": 10,
    "三十年份灵草": 35,
}

MARKET_GOODS = [
    {
        "name": "普通灵草",
        "price": 2,
        "effects": {"herbs": 1},
        "effect_text": "普通灵草+1",
    },
    {
        "name": "十年份灵草",
        "price": 10,
        "effects": {"aged_herbs_10": 1},
        "effect_text": "十年份灵草+1",
    },
    {
        "name": "三十年份灵草",
        "price": 35,
        "effects": {"aged_herbs_30": 1},
        "effect_text": "三十年份灵草+1",
    },
    {
        "name": "聚气散",
        "price": 20,
        "effects": {"cultivation_progress": 12},
        "effect_text": "修炼进度+12",
    },
    {
        "name": "回春丹",
        "price": 8,
        "effects": {"hp": 20},
        "effect_text": "气血恢复20",
    },
    {
        "name": "清心丸",
        "price": 22,
        "effects": {"heart_demon": -5},
        "effect_text": "心魔值-5",
    },
    {
        "name": "护身符",
        "price": 40,
        "effects": {"talisman_guard": 1},
        "effect_text": "护身符+1",
    },
    {
        "name": "火弹符",
        "price": 36,
        "effects": {"talisman_fire": 1},
        "effect_text": "火弹符+1",
    },
    {
        "name": "避火符",
        "price": 32,
        "effects": {"talisman_avoid_fire": 1},
        "effect_text": "避火符+1",
    },
    {
        "name": "破甲符",
        "price": 32,
        "effects": {"talisman_break_armor": 1},
        "effect_text": "破甲符+1",
    },
    {
        "name": "坊市情报",
        "price": 18,
        "effects": {"intelligence": 2, "exposure": 1},
        "effect_text": "情报值+2，暴露度+1",
    },
    {
        "name": "黑市线索",
        "price": 24,
        "effects": {"black_market_clue": 1, "exposure": 5},
        "effect_text": "黑市线索+1，暴露度+5",
    },
]

MONTHLY_EVENTS = [
    {
        "title": "族学点名",
        "text": "族学管事抽查旁支功课，你勉强答上几处经义。",
        "effects": {"contribution": 1, "righteous_reputation": 1},
    },
    {
        "title": "山雨伤田",
        "text": "青岭连夜大雨，灵田受损，主动帮忙的人被执事记了一笔。",
        "effects": {"contribution": 2, "physique": 1},
    },
    {
        "title": "坊市传闻",
        "text": "坊市有人议论旁支子弟近日进境，你听后收敛了几分行迹。",
        "effects": {"exposure": -2, "heart_demon": 1},
    },
    {
        "title": "旧祠冷香",
        "text": "夜里旧祠香火忽明忽暗，残破魂幡似在远处呼应。",
        "effects": {"demonic_qi": 1, "heart_demon": 1},
    },
    {
        "title": "族老讲法",
        "text": "一位族老在前堂讲解吐纳关窍，旁支也可旁听半日。",
        "effects": {"cultivation_progress": 5, "divine_sense": 1},
    },
    {
        "title": "大比风声",
        "text": "你听到几位直系弟子私下议论今年试炼的药点。",
        "effects": {"intelligence": 2},
    },
]
