# 事件池总规划

## 事件类型

- 月末事件。
- 地点遭遇。
- NPC 好感阶段事件。
- 路线识别事件。
- 风险反噬事件。
- 大比前事件。
- 结局后钩子。

## 触发条件

事件应根据以下字段触发：
- 月份。
- 地点或行动。
- NPC 好感。
- 路线资源。
- 暴露、心魔、魔气、业力。
- 黑水追踪。
- 盗术失败和结仇。
- 根基、熟练度、博学度、融会状态。

## 事件设计原则

多数事件只给文本和小幅变化。

少数事件给资源或解锁。

高收益事件必须有条件、风险或代价。

同类事件要有变体，避免重复刷屏。

## 配置化建议

事件配置可包含：
- id
- title
- trigger
- weight
- cooldown
- conditions
- effects
- text_success
- text_fail
- tags

## 标签建议

- family
- herb
- alchemy
- market
- heishui
- theft
- demonic
- relationship
- foundation
- tournament
- fate
