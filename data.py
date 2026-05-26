"""第一章《旁支入道》的静态数据。"""

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
        "modifiers": {"cultivation": 0, "physique": 1, "comprehension": 1, "combat_exp": 0},
        "growth": 0,
    },
    {
        "name": "四灵根",
        "weight": 28,
        "desc": "旁支常见资质，只要肯熬，也能在族中站稳脚跟。",
        "modifiers": {"cultivation": 1, "physique": 1, "comprehension": 1, "combat_exp": 0},
        "growth": 1,
    },
    {
        "name": "三灵根",
        "weight": 22,
        "desc": "修炼较顺，若有资源扶持，足以争一争大比名次。",
        "modifiers": {"cultivation": 2, "physique": 0, "comprehension": 1, "combat_exp": 1},
        "growth": 2,
    },
    {
        "name": "双灵根",
        "weight": 12,
        "desc": "资质不俗，即便出身旁支，也会被族老多看一眼。",
        "modifiers": {"cultivation": 3, "physique": 0, "comprehension": 2, "combat_exp": 1},
        "growth": 3,
    },
    {
        "name": "异灵根",
        "weight": 4,
        "desc": "灵机偏锋，悟性出众，但也容易惹来审视。",
        "modifiers": {"cultivation": 2, "physique": 0, "comprehension": 3, "combat_exp": 2},
        "growth": 3,
    },
]

NPCS = {
    "沈清婉": "旁支少女，常在藏书阁帮忙抄录旧册。",
    "沈怀远": "演武场管事，沉默寡言，重视勤勉。",
    "沈素秋": "灵田执事，做事细密，厌恶投机。",
    "沈砚": "同辈旁支子弟，心气颇高，常与人比较。",
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
    "1": "闭关修炼",
    "2": "演武练法",
    "3": "上山采药",
    "4": "照看灵田",
    "5": "古玉瓶催熟",
    "6": "炼制丹药",
    "7": "家族杂务",
    "8": "拜访族人",
    "9": "情意锁牵引",
    "10": "夜祭残幡",
    "11": "调息守心",
}

ATTRIBUTE_NAMES = {
    "cultivation": "修为",
    "physique": "体魄",
    "comprehension": "悟性",
    "combat_exp": "斗法",
    "herbs": "灵草",
    "spirit_stones": "灵石",
    "pills": "丹药",
    "contribution": "家族贡献",
    "exposure": "暴露度",
    "heart_demon": "心魔值",
    "demonic_qi": "魔气值",
    "karma": "业力值",
    "righteous_reputation": "正道声望",
}

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
        "text": "夜里旧祠香火忽明忽暗，残幡在识海深处一动。",
        "effects": {"demonic_qi": 1, "heart_demon": 1},
    },
    {
        "title": "族老讲法",
        "text": "一位族老在前堂讲解吐纳关窍，旁支也可旁听半日。",
        "effects": {"cultivation": 1, "comprehension": 1},
    },
]
