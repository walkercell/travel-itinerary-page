# trip.json 数据格式

`assets/template.html` 读取这一份 JSON 渲染整页。顶层字段都是可选的（`meta.title` 除外）：某个板块没有数据，页面就不显示它。可以从 `assets/trip-skeleton.json` 这份空白模板开始填。

下面的片段都只是**格式示意**：城市、航班、价格都是占位用的，不是真实行程。

## 目录

- [文本小语法](#文本小语法)
- [meta](#meta)
- [segments 和 route](#segments-和-route)
- [stats](#stats)
- [overview](#overview)
- [flights](#flights)
- [spots](#spots)
- [map](#map)
- [days](#days)
- [transport](#transport)
- [hotels](#hotels)
- [budget](#budget)
- [tips 和 disclaimer](#tips-和-disclaimer)

## 文本小语法

大部分文字字段支持两种标记，其余内容都会被转义，不能写 HTML：

- `**加粗**`
- `[[spotKey]]`：渲染成可以点开的景点按钮，`spotKey` 必须在 `spots` 里有定义

`build_page.py` 会检查每个 `[[...]]` 都能找到对应的景点。

## meta

```json
"meta": {
  "title": "城市 A + 城市 B 七日游",
  "pageTitle": "七日游行程",
  "subtitle": "5.1 出发 → 5.7 返回 · 2 位成人 · 轻松节奏",
  "people": 2,
  "currency": "¥",
  "storageKey": "my-trip-budget-v1"
}
```

- `pageTitle`：浏览器标签页上显示的标题。
- `people`：用来算"每人金额"。
- `storageKey`：浏览器里保存预算选择用的键名。每个行程用不同的值；数据结构大改后可以换一个新值，让旧的选择失效。

## segments 和 route

`segments` 定义行程分段和颜色，每天的标签、地图路线颜色、图例都会用到。

```json
"segments": [
  {"id": "a", "label": "城市 A", "color": "#c0392b"},
  {"id": "b", "label": "城市 B", "color": "#2a6fb0"},
  {"id": "fly", "label": "飞行", "color": "#5b5f97"}
]
```

`fly` 这个 id 有特殊用途：地图上航班虚线用它的颜色，图例里不单独列出。

`route` 是标题下面那一排路线标签：

```json
"route": [{"seg": "fly", "label": "出发地"}, {"seg": "a", "label": "城市 A 4晚"}, {"seg": "b", "label": "城市 B 2晚"}]
```

## stats

标题区的数字卡片。`value` 写成 `{{total}}` 或 `{{perPerson}}`，会自动替换成预算合计或每人金额，并跟着用户的预算选择实时更新。

```json
"stats": [
  {"value": "7 天 6 晚", "label": "5.1 出发，5.7 返回"},
  {"value": "{{total}}", "label": "2 人全包预算（按你的选择）"},
  {"value": "{{perPerson}}", "label": "折合每人"}
]
```

## overview

```json
"overview": [{"label": "一句话", "text": "……"}, {"label": "适合", "text": "……"}]
```

## flights

```json
{
  "no": "XX123",
  "tag": "去程",
  "airline": "示例航空",
  "aircraft": "Airbus A330",
  "status": "待预订",
  "from": {"code": "AAA", "city": "出发城市"},
  "to": {"code": "BBB", "city": "城市 A"},
  "depart": "2027-05-01T08:30:00+08:00",
  "departLabel": "5月1日 周六",
  "departTime": "08:30",
  "arriveLabel": "当天",
  "arriveTime": "12:45",
  "duration": "4 小时 15 分",
  "price": "往返约 ¥3,000/人"
}
```

`depart` 必须是带 UTC 时差的 ISO 时间，倒计时靠它计算。时差要用出发机场的当地时差。

## spots

景点字典。键是英文短 id，在文字里用 `[[键]]` 引用。

```json
"museum": {
  "name": "城市博物馆",
  "en": "City Museum",
  "img": "https://…/960px-….jpg",
  "desc": "两三句介绍：是什么、为什么值得去。",
  "ticket": "约 €15（≈¥120）；两个来源说法不一，待确认",
  "hours": "每天 9:00–17:00，**周一闭馆**",
  "stay": "1.5–2 小时",
  "tip": "开门就去，排队最短。"
}
```

- `img` 可以留空，之后运行 `scripts/wiki_images.py --trip trip.json --write` 自动补。
- `ticket` 写清楚价格的来源可信度：只有一个来源、各家差异大、估算，都要注明。

## map

```json
"map": {
  "places": {
    "airport-a": {"lat": 0.0, "lng": 0.0, "name": "城市 A 机场", "kind": "airport"},
    "museum": {"lat": 0.0, "lng": 0.0, "name": "城市博物馆", "kind": "spot", "spot": "museum"},
    "hotel-a": {"lat": 0.0, "lng": 0.0, "name": "城市 A 酒店", "kind": "hotel"}
  },
  "routes": {
    "5.2": ["hotel-a", "museum", "old-town"]
  },
  "airLegs": [["airport-a", "airport-b"]]
}
```

（坐标要填真实经纬度，上面的 0.0 只是占位。）

- `kind`：可选 `spot`、`hotel`、`airport`、`station`，决定全程视图里圆点的颜色。
- `spot`（可选）：在地图弹窗里加一个"看介绍"按钮，打开对应的景点卡片。
- `routes`：键必须和 `days[].date` 完全一致，值是当天按顺序经过的地点 id。有路线的那一天，标题栏会出现"🗺 地图"按钮。
- `airLegs`：航段两端的地点。地图上这两点之间画虚线，不画成实线路线。
- 坐标精度到小数点后 4 位就够了。拿不准的坐标，搜索"<地名> coordinates"核对一下。

## days

```json
{
  "date": "5.2",
  "weekday": "周日",
  "seg": "a",
  "title": "老城一日",
  "slots": [
    ["上午", "开门就进[[museum]]（1.5 小时），步行 10 分钟到[[old-town]]"],
    ["下午", "……"]
  ],
  "eat": "午：当地小馆 · 晚：夜市",
  "stay": "城市 A 酒店",
  "note": "博物馆周一闭馆，所以排在周日"
}
```

- `date` 用简短写法（`5.2`、`10.1`），在同一份行程里要唯一。
- `slots` 里每一项是 `[时间段, 文字]`。时间段可以写"清晨"、"上午"、"全天"等。

## transport

```json
"transport": {
  "columns": ["日期", "方式", "路线", "时间", "参考价"],
  "rows": [["5.1", "**XX123** 直飞", "出发城市 → 城市 A", "08:30 → 12:45", "¥3,000/人 往返"]],
  "note": "表格下方的说明文字"
}
```

## hotels

```json
{
  "img": "https://…",
  "name": "城市 A · 某酒店",
  "tag": "含早",
  "meta": "5.1–5.5 共 4 晚 · 四星 · 近地铁",
  "price": "参考价 **¥2,400**（4 晚，可免费取消）",
  "alt": "省钱备选：……",
  "url": "可选，预订链接"
}
```

## budget

```json
"budget": {
  "note": "汇率和说明",
  "items": [
    {
      "id": "airportIn",
      "cat": "交通",
      "name": "机场 → 酒店",
      "note": "5.1 中午落地",
      "verified": false,
      "options": [
        {"label": "机场大巴", "amount": 60, "detail": "约 ¥30/人"},
        {"label": "出租车", "amount": 200}
      ],
      "presets": {"eco": 0, "com": 1}
    },
    {
      "id": "tix",
      "cat": "门票",
      "name": "景点门票（多选）",
      "multi": true,
      "options": [{"label": "城市博物馆", "amount": 240, "detail": "¥120/人"}],
      "presets": {"eco": [0], "com": [0]}
    }
  ]
}
```

- `amount` 填全体人数的合计，不是单价。单价写在 `detail` 里，让人能自己核对。
- 单选项目的 `presets` 写一个序号；多选项目（`"multi": true`）写序号数组。
- 只有一个方案的项目（比如签证）不显示选项按钮，但金额仍然可以手动改。
- 类别按 `cat` 第一次出现的顺序分组显示。
- `verified: true` 显示"已查"，否则显示"估"。

## tips 和 disclaimer

```json
"tips": [{"title": "🌡️ 天气与穿衣", "items": ["……", "……"]}],
"disclaimer": "以上行程与价格基于公开信息整理，出行前请以官方实时信息（景区公告、车票机票、天气）为准。"
```
