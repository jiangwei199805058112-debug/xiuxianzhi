# 第一章装备与装备来源设计

> 第一章装备不应复杂到网游装备系统，而应服务于大比、路线差异、剧情反馈与后续伏笔。

## 一、装备系统定位

第一章装备目标：

1. 给玩家“我变强了”的直观反馈。
2. 让不同路线获得不同类型的准备。
3. 避免装备直接碾压修为、心境、路线积累。
4. 为第二章留下装备升级、炼器、黑水旧物、宗门法器等空间。

第一章适合做成：

```text
武器
法袍
护身物
法器旧物
符匣 / 丹炉 / 灵田工具
特殊奇遇道具
```

---

## 二、装备基础字段建议

```text
equipment_id
name
slot
rarity
source
price
description
effects
risk_tags
story_flags
```

| slot | 说明 |
|---|---|
| weapon | 武器 |
| robe | 法袍 |
| accessory | 护身物 / 玉佩 / 铜钱 |
| tool | 工具类，如丹炉、锄、符匣 |
| special | 奇遇道具 / 剧情物品 |

---

## 三、普通装备列表

### 旧木剑

```text
slot: weapon
rarity: common
source: 初始 / 家族杂物房
effect:
  大比基础战力 +1
```

### 练功木剑

```text
slot: weapon
rarity: common
source: 普通坊市 / 家族兑换
price: 2-4 下品灵石
effect:
  大比基础战力 +2
  木系术法练习效果 +小
```

### 铁脊短剑

```text
slot: weapon
rarity: uncommon
source: 普通坊市 / 黑水旧货
price: 6-10 下品灵石
effect:
  近战战力 +3
risk:
  黑水来源版本可能带追踪印
```

### 旧法袍

```text
slot: robe
rarity: common
source: 家族杂务 / 普通坊市 / 大比奖励
effect:
  受伤风险 -小
  大比防御评分 +1
```

### 青纹法袍

```text
slot: robe
rarity: uncommon
source: 普通坊市 / 家族奖励
price: 8-12 下品灵石
effect:
  防御评分 +3
  心境波动 -小
```

### 破旧护心玉

```text
slot: accessory
rarity: uncommon
source: 坊市旧货 / 天机阁线索
effect:
  抵消一次轻微受伤
  心魔事件判定 +小抗性
risk:
  可能是旧主遗物，引出小事件
```

### 清心玉佩

```text
slot: accessory
rarity: rare
source: 祖祠青灯 / 正修路线奖励 / 家族藏书阁
effect:
  心魔自然增长 -小
  魔道诱惑抗性 +中
  正修打坐收益 +小
```

---

## 四、路线专属装备 / 道具

### 正修打坐流：青灯残芯

```text
slot: special
rarity: unique
source: 祖祠青灯
effect:
  清明道心稳定度 +10
  打坐收益 +10%
  心魔事件抗性 +15%
risk:
  若接受魔道残物，可能触发青灯染墨
```

### 灵田经营流：青木旧锄

```text
slot: tool
rarity: unique
source: 地脉青木窖 / 沈若兰事件
effect:
  灵田照料收益 +1
  虫害风险 -小
  高年份灵草出现概率 +小
```

### 炼丹丹房流：裂纹试火炉

```text
slot: tool
rarity: unique
source: 裂炉生火
effect:
  炼丹成功率 +10%
  炉火感应触发
  炼丹失败时有概率保留半成品
risk:
  过度使用可能火气反噬 / 丹毒上升
```

### 盗术灰道流：窃运铜钱

```text
slot: accessory / special
rarity: unique
source: 沈青雀 / 盗术奇遇
effect:
  盗术成功率 +10%
  大比前可偷一点胜机
  对手首回合小概率失误
risk:
  因果痕迹 +中
  使用过多触发高阶追查
```

### 黑水投机流：黑契木盒

```text
slot: special
rarity: unique
source: 黑契盲盒
effect:
  解锁一次黑水特殊交易
  隐藏商人出现概率 +小
risk:
  黑水追踪 +中
  黑水人情债 +1
```

### 情报人情流：无字竹简

```text
slot: special
rarity: unique
source: 闻不语 / 情报奇遇
effect:
  情报购买成本 -小
  可提前识别一次假消息
  大比前获得对手弱点
risk:
  人情债累积
  秘密被闻不语掌握
```

### 魔道边缘流：黑玉残简

```text
slot: special
rarity: cursed
source: 百药山废洞 / 魔道残物
effect:
  短期修炼爆发 +高
  可解锁魔道残篇
  危急时可反杀
risk:
  魔道污染 +高
  心魔增长
  沈怀安警觉
  魔息外泄
```

### 坊市符箓流：残阵符匣

```text
slot: tool / accessory
rarity: unique
source: 坊市旧货 / 残阵符匣奇遇
effect:
  符箓失灵率 -中
  符箓携带上限 +1
  可组合低阶符箓形成小型连击
risk:
  外物依赖 +中
  修复需要材料
  大比入场检查可能限制
```

### 随心混合流：杂玉串

```text
slot: accessory
rarity: unique
source: 杂玉合鸣
effect:
  临场应变 +中
  多系统小幅收益 +小
  危机补救触发率 +小
risk:
  单项专精不足
  资源分散评价上升
```

---

## 五、不归楼相关装备 / 标记

### 不归楼印记

```text
slot: special
rarity: hidden
source: 启 / 不归楼强行灌顶
effect:
  修炼效率 +15%
  突破成功率 +小
  大比评分 +中
hidden:
  启的投资 = 1
  后续可触发梦中酒馆 / 怀表余音
risk:
  第一章不一定危险
  后期可能引出合作、收账、对抗或真相揭露
```

### 怀表碎片

```text
slot: special
rarity: unique
source: 不归楼 / 启的伏笔
effect:
  危机时可能触发一息时间错觉
  可作为第二章救场伏笔
risk:
  高阶存在可能识别其来源
```

### 魔界本源种

```text
slot: hidden_state
rarity: hidden
source: 不归楼强行灌顶
effect:
  经脉资质改善
  修炼效率提升
  魔道功法领悟提升
risk:
  伏笔版不立即魔化
  后期可能因心魔、魔道、启事件而激活
```

---

## 六、装备来源设计

| 来源 | 可产出装备 |
|---|---|
| 初始 / 家族杂物房 | 旧木剑、旧法袍 |
| 普通坊市 | 练功木剑、铁脊短剑、青纹法袍、护身玉 |
| 家族杂务 | 旧法袍、杂役工具、小护符 |
| 灵田事件 | 青木旧锄、灵田泥符 |
| 炼丹事件 | 裂纹试火炉、废丹残渣、火候笔记 |
| 天机阁 | 护心玉线索、无字竹简线索 |
| 沈青雀 | 窃运铜钱、敛息藏形诀 |
| 鬼手老陈 / 黑水 | 黑契木盒、黑水旧符、追踪印旧物 |
| 百药山废洞 | 黑玉残简、魔道残物 |
| 坊市旧货 | 残阵符匣、破旧护心玉 |
| 不归楼 | 不归楼印记、怀表余音、魔界本源种 |
| 家族大比奖励 | 内院听课令、青纹法袍、藏书阁资格 |

---

## 七、装备与路线关联

| 路线 | 核心装备 / 道具 |
|---|---|
| 正修打坐流 | 青灯残芯、清心玉佩 |
| 灵田经营流 | 青木旧锄、灵田泥符 |
| 炼丹丹房流 | 裂纹试火炉、火候笔记 |
| 盗术灰道流 | 窃运铜钱、敛息藏形诀 |
| 黑水投机流 | 黑契木盒、黑水旧符 |
| 情报人情流 | 无字竹简、密信残页 |
| 魔道边缘流 | 黑玉残简、魔纹骨片 |
| 坊市符箓流 | 残阵符匣、旧符袋 |
| 随心混合流 | 杂玉串、杂物包 |
| 不归楼隐藏线 | 不归楼印记、怀表碎片、魔界本源种 |

---

## 八、装备对比功能建议

```text
当前装备：
武器：旧木剑
法袍：旧法袍
饰品：无
工具：旧丹炉

可装备：
练功木剑
  战力 +2
  当前旧木剑：战力 +1
  替换后变化：战力 +1

青纹法袍
  防御 +3
  当前旧法袍：防御 +1
  替换后变化：防御 +2

残阵符匣
  符箓失灵率 -中
  当前无符匣
  替换后变化：开启符箓组合
```

推荐字段：

```text
equipped_items = {
  "weapon": None,
  "robe": None,
  "accessory": None,
  "tool": None
}
```
