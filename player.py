"""玩家数据与创建逻辑。"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Any, Dict, List

from data import ACTIONS_PER_MONTH, NPCS, SPIRIT_ROOTS, TOTAL_ACTIONS


def _weighted_random_root() -> Dict[str, Any]:
    total_weight = sum(root["weight"] for root in SPIRIT_ROOTS)
    roll = random.randint(1, total_weight)
    cursor = 0
    for root in SPIRIT_ROOTS:
        cursor += root["weight"]
        if roll <= cursor:
            return root
    return SPIRIT_ROOTS[0]


@dataclass
class Player:
    name: str
    spirit_root: str
    spirit_root_desc: str
    root_growth: int
    cultivation: int = 5
    physique: int = 5
    comprehension: int = 5
    combat_exp: int = 3
    herbs: int = 3
    spirit_stones: int = 5
    pills: int = 1
    contribution: int = 0
    exposure: int = 0
    heart_demon: int = 0
    demonic_qi: int = 0
    karma: int = 0
    righteous_reputation: int = 0
    npc_affection: Dict[str, int] = field(default_factory=dict)
    love_lock_level: int = 1
    soul_banner_awakened: bool = False
    souls_refined: int = 0
    total_actions: int = 0
    ending_flags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.npc_affection:
            self.npc_affection = {name: 10 for name in NPCS}
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

    def clamp(self) -> None:
        numeric_min_zero = [
            "cultivation",
            "physique",
            "comprehension",
            "combat_exp",
            "herbs",
            "spirit_stones",
            "pills",
            "contribution",
            "exposure",
            "heart_demon",
            "demonic_qi",
            "karma",
            "souls_refined",
            "total_actions",
        ]
        for attr in numeric_min_zero:
            if getattr(self, attr) < 0:
                setattr(self, attr, 0)

        self.exposure = min(self.exposure, 100)
        self.heart_demon = min(self.heart_demon, 100)
        self.demonic_qi = min(self.demonic_qi, 100)
        self.karma = min(self.karma, 100)
        self.righteous_reputation = max(-100, min(self.righteous_reputation, 100))
        self.total_actions = max(0, min(self.total_actions, TOTAL_ACTIONS))

        for npc in NPCS:
            self.npc_affection.setdefault(npc, 10)
        for npc, value in list(self.npc_affection.items()):
            self.npc_affection[npc] = max(0, min(int(value), 100))

    def advance_action(self) -> None:
        self.total_actions += 1
        self.clamp()

    def average_affection(self) -> float:
        if not self.npc_affection:
            return 0.0
        return sum(self.npc_affection.values()) / len(self.npc_affection)

    def status_text(self) -> str:
        affection_text = "，".join(f"{name}{value}" for name, value in self.npc_affection.items())
        return (
            f"姓名：{self.name}\n"
            f"出身：青岭沈家旁支\n"
            f"灵根：{self.spirit_root}（{self.spirit_root_desc}）\n"
            f"属性：修为{self.cultivation}｜体魄{self.physique}｜悟性{self.comprehension}｜斗法{self.combat_exp}\n"
            f"资源：灵草{self.herbs}｜灵石{self.spirit_stones}｜丹药{self.pills}｜家族贡献{self.contribution}\n"
            f"隐患：暴露度{self.exposure}｜心魔值{self.heart_demon}｜魔气值{self.demonic_qi}｜业力值{self.karma}\n"
            f"名声：正道声望{self.righteous_reputation}\n"
            f"NPC好感：{affection_text}\n"
            f"隐藏：情意锁低阶｜万魂幡炼魂次数{self.souls_refined}"
        )

    def to_dict(self) -> Dict[str, Any]:
        self.clamp()
        return {
            "name": self.name,
            "spirit_root": self.spirit_root,
            "spirit_root_desc": self.spirit_root_desc,
            "root_growth": self.root_growth,
            "cultivation": self.cultivation,
            "physique": self.physique,
            "comprehension": self.comprehension,
            "combat_exp": self.combat_exp,
            "herbs": self.herbs,
            "spirit_stones": self.spirit_stones,
            "pills": self.pills,
            "contribution": self.contribution,
            "exposure": self.exposure,
            "heart_demon": self.heart_demon,
            "demonic_qi": self.demonic_qi,
            "karma": self.karma,
            "righteous_reputation": self.righteous_reputation,
            "npc_affection": self.npc_affection,
            "love_lock_level": self.love_lock_level,
            "soul_banner_awakened": self.soul_banner_awakened,
            "souls_refined": self.souls_refined,
            "total_actions": self.total_actions,
            "ending_flags": self.ending_flags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        player = cls(
            name=str(data.get("name", "沈无名")),
            spirit_root=str(data.get("spirit_root", "五行杂灵根")),
            spirit_root_desc=str(data.get("spirit_root_desc", "旧存档未记录灵根说明。")),
            root_growth=int(data.get("root_growth", 0)),
            cultivation=int(data.get("cultivation", 5)),
            physique=int(data.get("physique", 5)),
            comprehension=int(data.get("comprehension", 5)),
            combat_exp=int(data.get("combat_exp", 3)),
            herbs=int(data.get("herbs", 3)),
            spirit_stones=int(data.get("spirit_stones", 5)),
            pills=int(data.get("pills", 1)),
            contribution=int(data.get("contribution", 0)),
            exposure=int(data.get("exposure", 0)),
            heart_demon=int(data.get("heart_demon", 0)),
            demonic_qi=int(data.get("demonic_qi", 0)),
            karma=int(data.get("karma", 0)),
            righteous_reputation=int(data.get("righteous_reputation", 0)),
            npc_affection=dict(data.get("npc_affection", {})),
            love_lock_level=int(data.get("love_lock_level", 1)),
            soul_banner_awakened=bool(data.get("soul_banner_awakened", False)),
            souls_refined=int(data.get("souls_refined", 0)),
            total_actions=int(data.get("total_actions", 0)),
            ending_flags=list(data.get("ending_flags", [])),
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
    player.clamp()
    return player
