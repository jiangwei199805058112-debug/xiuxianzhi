# 第一章事件配置化实施方案

> 版本：v0.1.25  
> 文档类型：实施方案 / 事件系统配置化 / 分阶段开发计划  
> 适用范围：第一章《旁支入道》事件系统、路线事件、大比事件、随机事件、危机补救事件  
> 当前状态：设计文档阶段，尚未要求立即修改运行代码  
> 参考优先级：  
> 1. `docs/canon/00_content_master.md`  
> 2. `docs/canon/06_npc_master.md`  
> 3. `docs/canon/07_chapter1_main_arc.md`  
> 4. `docs/canon/09_chapter1_route_event_chains.md`  
> 5. `docs/canon/10_chapter1_event_pool.md`  
> 6. `docs/canon/11_tournament_event_design.md`  
> 7. `docs/design/route_balance_notes.md`  
> 8. `docs/design/event_implementation_plan.md`

---

## 一、文档定位

本文件用于规划第一章事件系统如何从“策划文档”逐步进入“可运行代码与配置”。

当前第一章已经具备以下设计基础：

| 文档 | 内容 |
|---|---|
| `00_content_master.md` | 世界观、总设定母版 |
| `06_npc_master.md` | NPC主数据、关系变量、系统接口 |
| `07_chapter1_main_arc.md` | 第一章主线、月度结构、安全网 |
| `09_chapter1_route_event_chains.md` | 九条路线12个月事件链 |
| `10_chapter1_event_pool.md` | 第一章随机事件、路线事件、危机补救事件池 |
| `11_tournament_event_design.md` | 家族大比、对手、看台反应、结局衔接 |
| `route_balance_notes.md` | 路线强度、风险阈值、大比得分、模拟指标 |

本文件不直接写剧情事件正文，而是回答：

1. 事件系统应该如何拆模块？
2. 哪些内容先做，哪些后做？
3. JSON/配置结构应如何设计？
4. 如何保证旧存档兼容？
5. 如何避免一次性大改导致项目失控？
6. 每个阶段完成后应如何验证？
7. 哪些内容必须进入模拟器验证？

---

## 二、实施总原则

### 2.1 小步提交

事件系统不能一次性把所有内容接入。

推荐原则：

```text
一次只接入一个小系统。
一次只改少量文件。
每次改动都能运行。
每次接入后都能模拟。
```

禁止：

```text
一次性重写 systems.py
一次性新增所有路线事件
一次性改存档结构而不补迁移
一次性接入所有大比逻辑
一次性把文档全部转成配置
```

---

### 2.2 先配置，后复杂逻辑

第一阶段不追求复杂剧情演出，而应先打通：

```text
事件ID
触发条件
选项
变量变化
是否可重复
是否冷却
是否已触发
```

后续再逐步加入：

```text
NPC反应
路线权重
动态大比
看台演出
第二章继承
```

---

### 2.3 不破坏现有第一章控制台玩法

当前游戏已有第一章基础控制台玩法、黑水坊市、灵田、炼丹炉、装备、模拟器等内容。

事件配置化必须遵守：

1. 不删除现有入口。
2. 不破坏旧存档。
3. 不移除已有黑水坊市配置。
4. 不强行引入 GUI。
5. 不新增第二章实装内容。
6. 不引入复杂宗门系统。
7. 不大规模重构已稳定代码。

---

### 2.4 无模拟不提交

只要修改 Python 代码、配置文件、存档结构、数值、事件权重，就必须执行必要检查。

最低要求：

```bash
python -m py_compile main.py player.py systems.py data.py tournament.py simulate.py heishui_market.py cultivation_assets.py
python simulate.py
python simulate.py --runs 5
```

如果涉及数值平衡，建议额外执行：

```bash
python simulate.py --runs 200
```

如果只是纯文档更新，可以不运行模拟，但提交说明中必须写明：

```text
本次为纯文档更新，未修改运行逻辑，未运行模拟。
```

---

## 三、建议新增目录结构

未来进入配置化时，建议新增以下目录：

```text
configs/events/
configs/events/chapter1/
configs/events/chapter1/pools/
configs/events/chapter1/tournament/
configs/events/chapter1/routes/
```

建议文件规划：

```text
configs/events/chapter1/event_schema.json
configs/events/chapter1/monthly_rules.json
configs/events/chapter1/event_weights.json

configs/events/chapter1/pools/farm_events.json
configs/events/chapter1/pools/alchemy_events.json
configs/events/chapter1/pools/theft_events.json
configs/events/chapter1/pools/blackwater_events.json
configs/events/chapter1/pools/orthodox_events.json
configs/events/chapter1/pools/demonic_events.json
configs/events/chapter1/pools/market_events.json
configs/events/chapter1/pools/intel_events.json
configs/events/chapter1/pools/mixed_events.json
configs/events/chapter1/pools/crisis_recovery_events.json
configs/events/chapter1/pools/npc_reaction_events.json
configs/events/chapter1/pools/pre_tournament_events.json

configs/events/chapter1/tournament/tournament_flow.json
configs/events/chapter1/tournament/tournament_opponents.json
configs/events/chapter1/tournament/tournament_reactions.json
configs/events/chapter1/tournament/tournament_absent_events.json
configs/events/chapter1/tournament/tournament_endings.json

configs/events/chapter1/routes/route_tags.json
configs/events/chapter1/routes/route_detection_rules.json
```

---

## 四、建议新增代码模块

未来进入代码实现时，建议优先新增独立模块，避免继续膨胀 `systems.py`。

建议模块：

```text
event_engine.py
chapter1_events.py
chapter1_event_loader.py
chapter1_event_state.py
chapter1_tournament_events.py
```

### 4.1 `event_engine.py`

负责通用事件逻辑：

| 功能 | 说明 |
|---|---|
| 加载事件配置 | 从 JSON 读取事件 |
| 检查触发条件 | 根据玩家状态判断 |
| 选择可触发事件 | 按权重抽取 |
| 应用事件结果 | 修改玩家变量 |
| 处理冷却 | 防止事件过度重复 |
| 记录已触发事件 | 支持存档 |

---

### 4.2 `chapter1_event_loader.py`

负责第一章事件配置加载：

| 功能 | 说明 |
|---|---|
| 加载事件池 | 灵田、炼丹、盗术等 |
| 加载大比事件 | 对手、看台、结局 |
| 校验事件ID唯一性 | 防止重复ID |
| 校验字段完整性 | 防止配置缺字段 |
| 报错清晰 | 缺配置时明确提示 |

---

### 4.3 `chapter1_event_state.py`

负责事件状态与存档字段：

| 功能 | 说明 |
|---|---|
| 已触发事件 | `triggered_event_ids` |
| 事件冷却 | `event_cooldowns` |
| 月度事件记录 | `monthly_event_log` |
| 路线标签 | `route_tags` |
| 风险变量 | 盗术痕迹、丹毒、魔道污染等 |

---

### 4.4 `chapter1_events.py`

负责第一章非大比事件：

| 功能 | 说明 |
|---|---|
| 月末事件抽取 | 每月结束后触发 |
| NPC月度反应 | 根据玩家行为触发 |
| 危机补救事件 | 风险高时优先 |
| 随心混合流补救 | 误操作后触发 |
| 事件文本展示 | 控制台输出 |

---

### 4.5 `chapter1_tournament_events.py`

负责大比：

| 功能 | 说明 |
|---|---|
| 入场检查 | 检查资格、风险、物品 |
| 对手选择 | 根据路线和表现选择 |
| 大比阶段 | 初轮、中轮、关键战 |
| 看台反应 | NPC根据玩家表现反馈 |
| 结局衔接 | 第二章入口变量 |

---

## 五、推荐事件 JSON 基础结构

### 5.1 单事件结构

```json
{
  "event_id": "EVT_CH1_POOL_FARM_001_FIELD_INSECT",
  "title": "灵田虫痕",
  "event_type": "farm_random",
  "chapter": 1,
  "month_min": 2,
  "month_max": 12,
  "repeatable": true,
  "cooldown_months": 2,
  "priority": 4,
  "weight": 10,
  "risk_level": "low",
  "route_tags": ["farming", "mixed_random"],
  "npc_ids": ["NPC_SHEN_RUOLAN_001"],
  "conditions": [
    {
      "field": "has_spirit_field",
      "op": "==",
      "value": true
    },
    {
      "field": "field_care_this_month",
      "op": "<=",
      "value": 0
    }
  ],
  "text": "玩家在田埂边发现几片被咬碎的清心叶，叶背还有细小虫卵。",
  "choices": [
    {
      "choice_id": "manual_remove",
      "label": "手动除虫",
      "effects": [
        {
          "field": "pest_risk",
          "op": "add",
          "value": -10
        },
        {
          "field": "farming_skill",
          "op": "add",
          "value": 1
        }
      ]
    },
    {
      "choice_id": "ignore",
      "label": "暂时不管",
      "effects": [
        {
          "field": "crop_wither_risk",
          "op": "add",
          "value": 10
        }
      ]
    }
  ]
}
```

---

### 5.2 条件字段建议

| 字段 | 说明 |
|---|---|
| `field` | 玩家字段、路线变量或事件状态 |
| `op` | 判断方式 |
| `value` | 判断值 |

支持的 `op` 建议：

```text
==
!=
>
>=
<
<=
in
not_in
contains
not_contains
exists
not_exists
```

---

### 5.3 效果字段建议

| 字段 | 说明 |
|---|---|
| `field` | 要修改的变量 |
| `op` | 修改方式 |
| `value` | 修改值 |

支持的 `op` 建议：

```text
set
add
min
max
append
remove
flag_on
flag_off
```

---

## 六、玩家存档字段规划

未来若接入事件系统，需要在 `player.py` 中新增字段时，必须保持旧存档兼容。

### 6.1 事件状态字段

建议新增：

```python
triggered_event_ids: list[str]
event_cooldowns: dict[str, int]
monthly_event_log: list[dict]
route_tags: list[str]
```

### 6.2 风险变量字段

建议新增或统一：

```python
theft_trace_level: int
blackwater_debt: int
blackwater_trace_level: int
demonic_contamination: int
pill_toxin_level: int
public_scandal_level: int
field_pollution_level: int
consumable_dependency_level: int
resource_scatter_level: int
```

### 6.3 路线变量字段

建议新增或统一：

```python
orthodox_path_level: int
farming_path_level: int
alchemy_path_level: int
theft_path_level: int
blackwater_path_level: int
intel_social_path_level: int
demonic_path_level: int
market_talisman_path_level: int
mixed_path_score: int
```

### 6.4 兼容规则

新增字段必须遵守：

1. 旧存档载入时自动补默认值。
2. 默认值不得让旧玩家突然进入危机。
3. 新字段不得覆盖旧字段。
4. 删除字段只能废弃，不应直接删除。
5. 任何存档字段变更必须做旧存档 smoke check。

---

## 七、路线识别规则

未来事件系统需要根据玩家行为判断路线倾向。

### 7.1 路线行为映射

| 行为 | 路线倾向 |
|---|---|
| 打坐修炼 | 正修打坐流 |
| 照料灵田 | 灵田经营流 |
| 炼丹/复盘废丹 | 炼丹丹房流 |
| 偷窃/潜行/藏物 | 盗术灰道流 |
| 黑水购买/盲盒/债务 | 黑水投机流 |
| 买情报/控风评 | 情报人情流 |
| 接触魔道残物/魔功 | 魔道边缘流 |
| 普通坊市买符/倒卖 | 坊市符箓流 |
| 多系统浅尝 | 随心混合流 |

---

### 7.2 Mixed_Path 判定

第10月后，如果满足多数条件，可标记：

```text
Mixed_Path
```

建议条件：

| 条件 |
|---|
| 接触过3个以上系统 |
| 没有任一主路线达到高阶专精 |
| 没有严重公开丑闻 |
| 没有深度魔道污染 |
| 没有与核心 NPC 全面决裂 |
| 资源投入分散 |

---

### 7.3 路线锁定原则

路线标签不是强制排他。

玩家可以同时拥有：

```text
farming + alchemy
theft + blackwater
orthodox + intel
mixed + market
```

但高阶专属事件应检查：

1. 主路线投入是否足够。
2. 风险是否过高。
3. NPC关系是否达标。
4. 是否被冲突路线破坏。

---

## 八、事件触发流程建议

每月结束时，可按以下流程处理事件：

```text
1. 更新月度行为统计
2. 计算路线倾向
3. 衰减部分隐性风险
4. 检查强制危机事件
5. 检查NPC月度反应
6. 检查路线专属事件
7. 抽取随机事件
8. 检查随心混合流补救
9. 更新事件冷却
10. 写入月度事件日志
```

### 8.1 风险衰减

部分风险应自然衰减：

| 风险 | 衰减条件 |
|---|---|
| 盗术痕迹 | 停止盗术、处理赃物 |
| 黑水追踪 | 洗掉标记、减少交易 |
| 公开流言 | 无新丑闻 |
| 心境压力 | 打坐、柳听弦调心 |
| 灵田虫害 | 照料、驱虫 |
| 资源分散 | 连续投入单路线 |

魔道污染、黑水债务、丹毒不应轻易自然消失，应需要事件或行动处理。

---

### 8.2 危机优先

如果危机变量超过阈值，应优先触发危机事件。

示例：

```text
theft_trace_level >= 80 → 盗术危机
demonic_contamination >= 80 → 魔气外泄
blackwater_debt >= 80 → 黑水逼债
pill_toxin_level >= 80 → 丹毒反噬
```

---

## 九、实施阶段规划

### v0.1.26：事件系统字段与空引擎

目标：只打基础，不接入大量事件。

建议内容：

1. 新增事件状态字段。
2. 新增事件引擎空框架。
3. 新增事件配置目录。
4. 增加配置加载和校验。
5. 不接入复杂事件池。
6. 保证旧存档兼容。
7. simulate.py 不应明显变化。

验收：

```bash
python -m py_compile main.py player.py systems.py data.py tournament.py simulate.py heishui_market.py cultivation_assets.py
python simulate.py
python simulate.py --runs 5
```

---

### v0.1.27：灵田与炼丹事件池 MVP

目标：先接入低风险、正向反馈较多的事件池。

建议接入：

| 事件池 | 原因 |
|---|---|
| 灵田虫害 | 已有灵田系统，容易落地 |
| 田土发白 | 可增加经营感 |
| 沈若兰巡田 | NPC反馈 |
| 一炉焦黑 | 已有炼丹失败 |
| 火候灵光 | 炼丹正反馈 |
| 丹毒微苦 | 风险提示 |

不建议本阶段接入：

```text
魔道危机
黑水债务
大比重构
复杂情报
大型NPC关系网
```

验收重点：

1. 事件能触发。
2. 事件不会刷屏。
3. 不破坏旧炼丹和灵田逻辑。
4. simulate.py 结果不应大幅膨胀。

---

### v0.1.28：盗术、黑水、坊市风险事件

目标：接入灰色风险和普通坊市动态。

建议接入：

| 事件池 | 重点 |
|---|---|
| 盗术痕迹 | 未发现不公开惩罚 |
| 青雀警告 | 价值观边界 |
| 黑水假货 | 黑水风险 |
| 标记黑货 | 追踪风险 |
| 坊市涨价 | 价格波动 |
| 符纸失灵 | 外物风险 |

验收重点：

1. 偷窃未暴露不应直接增加公开惩罚。
2. 黑水收益必须伴随风险。
3. 坊市不能重新变成无脑强路线。
4. 风险变量应能衰减或补救。

---

### v0.1.29：情报、人情、随心混合补救

目标：让真实玩家行为获得反馈。

建议接入：

| 事件池 | 重点 |
|---|---|
| 旁支流言 | 情报入门 |
| 假消息 | 情报判断 |
| 闻不语开价 | 信用系统 |
| 柳听弦调心 | 心境恢复 |
| 小补救 | 误操作补救 |
| 小组合 | 杂学反馈 |
| 临场应变 | 适应性天赋前置 |

验收重点：

1. 情报不直接替代战斗力。
2. 随心混合流有反馈但不碾压专精。
3. 人情债和信用应留下后续变量。
4. 成人情缘相关必须遵守镜头外处理和自愿原则。

---

### v0.1.30：魔道边缘事件

目标：接入魔道诱惑与回正机制。

建议接入：

| 事件 | 重点 |
|---|---|
| 黑梦 | 轻度提示 |
| 经脉异动 | 使用魔物反馈 |
| 怀安察觉 | 回正机会 |
| 清心压制 | 补救 |
| 墨阳低语 | 高风险诱惑 |
| 魔气外泄 | 高危事件 |

验收重点：

1. 轻度魔道可回头。
2. 中度魔道需要代价。
3. 重度魔道进入逃亡/边缘线。
4. 魔道强度不能成为无脑通关。
5. 沈怀安与沈墨阳形成正反拉扯。

---

### v0.1.31：大比事件 MVP

目标：先接入简化版大比流程，不重写所有战斗。

建议接入：

| 阶段 | 内容 |
|---|---|
| 入场检查 | 检查符箓、丹毒、痕迹、污染 |
| 对手选择 | 简化对手池 |
| 路线加成 | 根据路线变量加分 |
| 风险扣分 | 丹毒、污染、外物依赖 |
| 看台反应 | 简短文本 |
| 结局标签 | 第二章入口变量 |

验收重点：

1. 大比仍能正常完成。
2. 不同路线有不同表现。
3. 随心混合流有保底。
4. 魔道/盗术/黑水有审查风险。
5. 前十率、前三率、第一率符合 `route_balance_notes.md` 目标区间。

---

## 十、推荐开发顺序

推荐顺序：

```text
1. 事件状态字段
2. 事件配置加载器
3. 事件触发器
4. 灵田/炼丹低风险事件
5. 盗术/黑水/坊市风险事件
6. 情报/随心补救事件
7. 魔道边缘事件
8. 大比事件 MVP
9. 大比看台反应
10. 第二章继承变量
```

不推荐顺序：

```text
1. 先做魔道大系统
2. 先重写大比
3. 先把所有事件配置化
4. 先做复杂情缘事件
5. 先做第二章
```

---

## 十一、配置校验规则

未来事件配置加载时，必须校验：

| 校验项 | 说明 |
|---|---|
| event_id 唯一 | 不允许重复 |
| title 存在 | 事件必须有名称 |
| event_type 存在 | 事件必须分类 |
| month 范围合法 | 1-12 |
| choices 非空 | 除纯文本事件外必须有选项 |
| effects 字段合法 | 不允许修改未知字段 |
| route_tags 合法 | 必须在路线表中 |
| npc_ids 合法 | 必须在 NPC 主数据中 |
| repeatable 合法 | 布尔值 |
| cooldown 合法 | 非负整数 |

配置错误时，必须清晰报错，例如：

```text
[EventConfigError] EVT_CH1_POOL_FARM_001_FIELD_INSECT missing choices
[EventConfigError] Duplicate event_id: EVT_CH1_POOL_FARM_001_FIELD_INSECT
[EventConfigError] Unknown npc_id: NPC_UNKNOWN
```

---

## 十二、事件文本规范

### 12.1 文本风格

第一章事件文本应遵守：

1. 简洁。
2. 有修仙氛围。
3. 不堆砌设定。
4. 结果明确。
5. 不写太长对话。
6. 适合控制台阅读。

### 12.2 成人情缘边界

若事件涉及成人情缘，必须遵守：

1. 角色 18 岁以上。
2. 双方自愿。
3. 不写强迫、胁迫、精神控制。
4. 亲密过程镜头外处理。
5. 不写露骨性动作、器官、体液、插入、姿势过程。
6. 重点写关系、信任、情债、声誉风险、双修收益和后果。

参考：

```text
docs/design/romance_relationship_system.md
```

---

## 十三、模拟验收计划

每次事件系统改动后，应至少记录：

| 指标 | 说明 |
|---|---|
| 平均名次 | 是否路线强度变化 |
| 前十率 | 是否过强/过弱 |
| 前三率 | 是否高光过多 |
| 第一率 | 是否夺冠过易 |
| 平均风险 | 灰色/魔道是否有代价 |
| 事件触发率 | 事件是否存在感足 |
| 危机触发率 | 风险是否有效 |
| 补救触发率 | 是否不死路 |
| 随心流表现 | 真实玩家是否能活 |
| 黑水收益 | 是否过强 |
| 坊市符箓收益 | 是否过稳 |

---

## 十四、阶段提交模板

未来 Codex 完成事件系统相关任务时，建议回复格式：

```text
已完成 vX.X.X。

修改文件：
- ...

本次是否修改 Python 代码：是/否
本次是否修改配置：是/否
本次是否修改存档结构：是/否
本次是否修改黑水坊市配置：是/否

验证：
- py_compile：通过/不适用
- python simulate.py：通过/不适用
- python simulate.py --runs 5：通过/不适用
- 额外模拟：...

关键结果：
- ...

git status --short：
...
提交：
...
推送：
...
```

---

## 十五、风险控制清单

任何事件系统实现前必须检查：

| 检查项 | 是否必须 |
|---|---|
| 是否会破坏旧存档 | 必须检查 |
| 是否新增字段默认值 | 必须 |
| 是否修改黑水配置 | 若修改必须说明 |
| 是否影响 simulate.py | 必须 |
| 是否导致路线过强 | 必须模拟 |
| 是否导致随心流死路 | 必须模拟 |
| 是否有无成本刷资源 | 必须检查 |
| 是否有不可恢复惩罚 | 必须检查 |
| 是否有未授权删除 | 必须禁止 |
| 是否 force push | 禁止 |

---

## 十六、第一批最适合实现的事件

建议第一批进入代码的事件不要太复杂。

### P0 推荐事件

| 事件ID | 原因 |
|---|---|
| `EVT_CH1_POOL_FARM_001_FIELD_INSECT` | 灵田已有基础，低风险 |
| `EVT_CH1_POOL_FARM_004_RUOLAN_PATROL` | 增加沈若兰反馈 |
| `EVT_CH1_POOL_ALCHEMY_001_BURNT_POT` | 炼丹失败已有基础 |
| `EVT_CH1_POOL_ALCHEMY_003_PILL_TOXIN_WARNING` | 控制丹药路线 |
| `EVT_CH1_POOL_MARKET_001_PRICE_SHIFT` | 坊市动态 |
| `EVT_CH1_POOL_MIXED_001_SMALL_RECOVERY` | 误操作补救 |

### P1 推荐事件

| 事件ID | 原因 |
|---|---|
| `EVT_CH1_POOL_THEFT_005_TRACE_DECAY` | 实现未暴露不公开惩罚 |
| `EVT_CH1_POOL_BLACKWATER_001_FAKE_GOODS` | 黑水风险 |
| `EVT_CH1_POOL_INTEL_002_FALSE_NEWS` | 情报判断 |
| `EVT_CH1_POOL_DEMONIC_001_BLACK_DREAM` | 魔道提示 |
| `EVT_CH1_PRE_TOUR_008_MIXED_PATCHWORK` | 随心流保底 |

### P2 推荐事件

| 事件ID | 原因 |
|---|---|
| `EVT_CH1_POOL_THEFT_006_EVIDENCE_FOUND` | 盗术危机 |
| `EVT_CH1_POOL_BLACKWATER_004_DEBT_CALL` | 黑水债务 |
| `EVT_CH1_POOL_DEMONIC_006_PUBLIC_TAINT` | 魔道危机 |
| `EVT_CH1_POOL_INTEL_006_SECRET_LEAK` | 情报危机 |
| `EVT_CH1_TOUR_001_ENTRY_CHECK` | 大比检查 |

---

## 十七、禁止一次性实装清单

以下内容不要在同一个版本一次性完成：

```text
完整事件引擎
全部事件池
完整大比重构
完整NPC关系网
完整情缘事件
完整魔道线
完整第二章入口
完整配置迁移
```

建议每次只做一个可验证目标。

---

## 十八、和现有系统的衔接建议

### 18.1 与 `systems.py`

`systems.py` 当前承载大量第一章行动逻辑。  
事件系统接入时，应尽量通过函数调用新增事件，而不是重写现有系统。

建议方式：

```text
行动完成后记录月度行为
月末调用事件系统
事件系统根据行为触发事件
事件结果写回 player
```

---

### 18.2 与 `player.py`

`player.py` 负责存档字段。  
新增字段时必须提供默认值和旧存档兼容。

建议方式：

```text
Player.__init__ 添加默认字段
load 时补齐缺失字段
旧存档 smoke check
```

---

### 18.3 与 `simulate.py`

`simulate.py` 是平衡验证核心。  
事件系统接入后，模拟器必须能：

1. 跳过交互式文本。
2. 自动选择事件选项。
3. 记录事件触发次数。
4. 输出路线风险指标。
5. 输出随心流系统接触数量。

---

### 18.4 与 `heishui_market.py`

黑水坊市已有配置驱动。  
事件系统不应破坏现有黑水配置。

未来黑水事件可读取：

```text
黑水商誉
黑水债务
黑水购买次数
黑水追踪标记
盲盒结果
```

但不应直接改动现有黑水商品配置，除非任务明确要求。

---

### 18.5 与 `tournament.py`

大比事件 MVP 可以先不重写 `tournament.py`，而是在现有评分前后加入：

```text
入场检查
路线加成
风险扣分
NPC反应文本
结局标签
```

等 MVP 稳定后，再考虑更细的对手战流程。

---

## 十九、验收标准

### v0.1.26 空引擎验收

| 标准 | 要求 |
|---|---|
| 旧玩法 | 可正常进入 |
| 旧存档 | 可载入 |
| simulate.py | 可运行 |
| 事件配置 | 能加载或明确报错 |
| 未接事件 | 不影响结果 |

### v0.1.27 低风险事件验收

| 标准 | 要求 |
|---|---|
| 灵田事件 | 可触发 |
| 炼丹事件 | 可触发 |
| 事件频率 | 不刷屏 |
| 路线强度 | 不明显膨胀 |
| 旧存档 | 兼容 |

### v0.1.31 大比事件验收

| 标准 | 要求 |
|---|---|
| 九条路线 | 均可结算 |
| 随心流 | 有保底 |
| 风险路线 | 有代价 |
| 大比缺席 | 有替代 |
| 前十率 | 符合目标区间 |
| 第一率 | 不应过高 |

---

## 二十、收束说明

第一章事件配置化的目标不是一次性做出庞大系统，而是逐步把已经完成的文档内容安全接入游戏。

最终理想状态：

```text
文档定义世界观和设计边界
JSON配置定义事件数据
event_engine.py 负责触发和执行
simulate.py 负责平衡验证
player.py 负责状态和存档
systems.py 保留行动入口
tournament.py 负责大比结算
```

开发过程中必须始终遵守：

```text
不破坏旧存档
不一次性大改
不让高风险路线无成本变强
不让随心玩家死路
不让符箓/黑水/魔道变成无脑最优
不提交未授权文件
不 force push
无模拟不提交
```

本文件作为后续 v0.1.26 之后事件系统实装的路线图。
