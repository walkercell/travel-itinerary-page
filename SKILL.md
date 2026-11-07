---
name: travel-itinerary-page
description: >-
  Plan a multi-city trip end to end and deliver it as one shareable, mobile-friendly HTML page:
  real flight numbers and prices for flexible dates, hotel picks, a day-by-day route with
  clickable attraction cards (photo, intro, ticket price, opening hours), a real map that shows
  each day's route, and an all-in budget where every cost line can be switched between options
  or edited. Use this skill whenever someone wants a travel plan, itinerary, 行程, 攻略, 旅行计划,
  旅游路线, trip budget, or "make my trip into a web page", even if they only mention dates and a
  destination, or want flights + hotels + route planned together.
---

# Travel Itinerary Page

把一次旅行从"想去哪"做到"一个能直接打开、能分享的行程网页"。产出是**一个单文件 HTML**：页面结构由 `assets/template.html` 统一渲染，你只需要准备一份行程数据 `trip.json`。

这样分工是为了**可复现**：网页样式和交互已经调好、测过，每次只换数据，不重新写前端，结果稳定、也省时间。

## 产出长什么样

从上到下依次是：

1. **标题区**：路线标签、天数、预算合计、每人金额
2. **航班卡片**：可左右滑动，显示航班号、机型、起降时间、时长、参考价、"待预订"状态和起飞倒计时
3. **行程总览**
4. **真实地图**：可以看全程，也可以按天切换路线，标出当天的游览顺序；点景点能打开介绍
5. **每日行程**：分上午、下午、晚上；景点是按钮，点开有图片、介绍、门票、开放时间和小贴士；每天另附餐饮、住宿和备注
6. **交通总览表**
7. **住宿卡片**
8. **预算**：每一项都能选方案（门票和活动可以多选），也能直接改金额；有省钱 / 舒适两个一键方案，选择会记在浏览器里
9. **实用贴士和免责声明**

## 工作流程

按顺序做。每一步都把查到的事实写进 `trip.json` 的对应字段，字段说明见 `references/data-format.md`，可以从 `assets/trip-skeleton.json` 开始填。

### 1. 一次问全关键信息

缺少的信息一次性问完，不要一轮轮追问：

- 出发地、目的地（可以多个城市）
- 日期窗口，以及能接受前后浮动几天：这决定能不能挑到便宜机票
- 人数、同行人类型、预算档位、偏好（人文、自然、美食、拍照、户外等）、节奏（轻松还是紧凑）
- 酒店偏好：品牌、档次、位置
- 必去的地方和必做的事

用户没说的用合理默认值（2 位成人、舒适档），在交付时说明用了哪些假设。

### 2. 机票：查真实航班号和价格

具体查法见 `references/research-playbook.md` 的"机票"一节。要点：

- 在浮动范围内比较几组出发和返回日期，记下每组最低价，告诉用户哪天最便宜、为什么。
- 每段航班都要记下：航班号、机型、起飞和到达时间（带 UTC 时差，倒计时要用）、飞行时长、参考价。
- 选航班时考虑落地时间能不能接上酒店入住，避免为了早到或晚走多订一晚。
- 多城市行程的城际交通也要查班次。有两个机场的城市，要看清用的是哪一个。

### 3. 住宿：按偏好选，给出备选

- 有酒店搜索工具（例如 RollingGo 的 MCP）就用它查实时价格和房型；没有就用网页搜索或酒店官网。
- 每个地方给一个推荐，再给一个省钱备选；写清价格、位置优势、能不能免费取消。
- 某地没有用户偏好的品牌时，直说，然后给替代选择。

### 4. 每日行程和景点资料

规划原则见 `references/planning-rules.md`。要点：

- 按地理顺路串景点，每天 3–5 个点；标出每个点大概停留多久，体力不够时可以删哪几个。
- 先查好开放规律（哪天闭馆、宗教场所的礼拜时间、节假日）再排日期，不要排到闭馆那天。
- 受天气影响的项目要留备用日；长途回程前留半天到一天休息。
- 每个景点写成 `spots` 里的一项：介绍、门票、开放时间、建议停留时间、小贴士。
  门票价格要搜索核实；几个来源说法不一致时，写成区间并注明"待确认"。
- 图片：运行 `python3 scripts/wiki_images.py --trip trip.json --write`，自动从 Wikimedia 填景点图片。抽查几张，确认图里确实是这个地方。

### 5. 预算：每一项都给方案，让用户自己选

用户最在意价格准不准。所以：

- 每笔花销都是一个 `budget.items` 项。有多种走法的要列出方案让用户选，例如机场接驳车、出租车、预约接机。门票和活动用多选。
- 金额统一按全体人数算。在 `note` 或 `detail` 里写清单价和次数（例如"¥75/人/来回 × 4 次"），让用户能自己核对。
- 实时查到的价格标 `"verified": true`，估算的不标，页面会显示"估"字。不要把估算说成已经核实。
- 类别要全：机票、机场往返、市内交通、城际交通、住宿、餐饮（按天）、门票、活动、签证、上网、保险、纪念品、零碎开销。
- 给每项配好 `presets.eco` 和 `presets.com`，"省钱方案"和"舒适方案"两个按钮才有意义。

### 6. 生成、校验、交付

```bash
python3 scripts/build_page.py trip.json -o <输出路径>.html
```

脚本会先校验数据：引用的景点、地点、日期都要存在，预算方案的序号不能越界，航班时间必须带时差。报错就改数据再跑，直到通过。

然后在浏览器里打开生成的页面，至少检查这几项：

- 航班倒计时在走
- 地图底图能加载，按天切换正常
- 随便点两个景点，弹窗有图、有门票信息
- 切换一个预算方案，合计会跟着变

交付时告诉用户：

- 文件路径
- 一句话行程概要和预算区间
- 哪些价格是估算的
- 哪些还没订

**不要替用户下单或付款**：预订和购票都要用户明确确认后才做。

## 用户常见的后续修改

- **改行程**（少一天、提前回城、加休息日）：改 `days`、`map.routes`、`flights`，以及受影响的住宿和预算项，然后重新构建。
- **觉得价格不准**：把这一项拆成多个方案，或者补上单价说明。用户也可以直接在页面上改金额。
- **换底图**：在 `assets/template.html` 里搜索 `tileLayer`，替换瓦片地址。不要用要 API key 的服务；`references/research-playbook.md` 里有说明。

## 文件

| 路径 | 用途 |
|---|---|
| `assets/template.html` | 页面模板，所有板块从数据渲染；不需要的板块，数据留空就不显示 |
| `assets/trip-skeleton.json` | 空白数据模板，内容都是占位，复制一份开始填 |
| `scripts/build_page.py` | 校验 `trip.json` 并生成 HTML（只用 Python 标准库） |
| `scripts/wiki_images.py` | 从 Wikipedia / Wikimedia Commons 找景点图片 |
| `references/data-format.md` | `trip.json` 字段说明，写数据前必读 |
| `references/research-playbook.md` | 机票、酒店、门票、汇率、图片、地图的查法和坑 |
| `references/planning-rules.md` | 行程编排、预算拆分、贴士的原则 |
