# Travel Itinerary Page

> 一个 AI Agent Skill：把"想去哪、哪几天、几个人"变成一个**能直接打开、能分享的行程网页**。网页里有真实航班、酒店推荐、景点卡片、按天切换的路线地图，以及可以逐项自选的全包预算。
>
> An agent skill that plans a trip end to end — real flights, hotel picks, day-by-day route, clickable attraction cards, a real map, and an editable all-in budget — and ships it as one self-contained HTML page.

## 页面里有什么

| 板块 | 说明 |
|---|---|
| ✈️ 航班卡片 | 航班号、机型、起降时间、飞行时长、参考价、"待预订"状态，以及实时的起飞倒计时 |
| 🗺️ 路线地图 | 真实街道地图（Leaflet + Esri 底图，不需要 API key）。可以看全程，也可以按天看路线，数字标出当天的游览顺序 |
| 🗓️ 每日行程 | 上午、下午、晚上的安排，加上餐饮和住宿；景点是按钮，点开有图片、介绍、门票、开放时间、小贴士 |
| 🚆 交通 / 🏨 住宿 | 交通总览表，酒店卡片附推荐和省钱备选 |
| 💰 预算 | 每一项都能选方案（接驳车还是打车、住哪家、吃什么档次），门票和活动可以多选，金额可以直接改；有省钱 / 舒适两个一键方案；选择保存在浏览器本地 |
| 🎒 贴士 | 天气穿衣、证件预订、避坑、安全，以及结尾的免责声明 |

页面会自动适配手机和深色模式。

## 安装

把整个文件夹放进你的 Agent 的 skills 目录。以 Claude Code 为例：

```bash
git clone https://github.com/walkercell/travel-itinerary-page ~/.claude/skills/travel-itinerary-page
```

装好后开一个新会话，Agent 就能用这个技能了。

## 怎么用

直接跟 Agent 说你的计划，例如：

- "五一想从上海去日本关西玩 6 天，日期可以前后浮动 2 天找便宜机票，帮我排行程并查可以订的航班号。"
- "两个人下个月去巴塞罗那 + 里斯本一周，预算中等，帮我做成一个手机上能看的行程网页。"
- "把我们的东京 5 日行程做成网页，每个景点能点开看门票。"

Agent 会按 `SKILL.md` 的流程走：一次问全信息 → 查机票 → 查酒店 → 排每日行程、核实门票 → 拆预算 → 生成网页并在浏览器里检查。

## 不用 Agent，自己生成

```bash
# 复制空白模板，填好你的行程
cp assets/trip-skeleton.json my-trip.json

# 给景点自动找图片（Wikipedia / Wikimedia Commons）
python3 scripts/wiki_images.py --trip my-trip.json --write

# 校验数据并生成网页（只需要 Python 3.9+，不用装任何依赖）
python3 scripts/build_page.py my-trip.json -o my-trip.html
```

字段说明见 [`references/data-format.md`](references/data-format.md)。

## 目录结构

```
travel-itinerary-page/
├── SKILL.md                     # 给 Agent 看的工作流程
├── assets/
│   ├── template.html            # 页面模板（所有板块都从数据渲染）
│   └── trip-skeleton.json       # 空白数据模板（内容都是占位）
├── scripts/
│   ├── build_page.py            # 校验 + 生成 HTML
│   └── wiki_images.py           # 找景点图片
└── references/
    ├── data-format.md           # trip.json 字段说明
    ├── research-playbook.md     # 机票、酒店、门票、图片、地图的查法和坑
    └── planning-rules.md        # 行程编排和预算原则
```

## 依赖与可选工具

- **必需**：Python 3（只用标准库）。查看页面时需要联网，用来加载地图、地图库和景点图片。
- **建议**：
  - 网页搜索：核实门票、汇率、开放时间
  - 浏览器自动化：查 Google 机票的实时航班和价格
- **可选**：
  - 酒店搜索工具，例如 RollingGo 的 MCP，可以查实时房价和房型
  - 没有的话，Agent 会改用网页搜索或酒店官网

## 注意

- 页面上的价格分两种："已查"是生成页面时实时查到的，"估"是按攻略估算的。出行前请以官方实时信息为准。
- 这个技能不会替你下单或付款；预订和购票都要你自己确认。
- 公开发布你自己的行程页之前，检查一下有没有不想公开的信息，比如订单号、住址、联系方式。

## License

[MIT](LICENSE)。地图数据 © OpenStreetMap contributors，底图 © Esri；景点图片来自 Wikimedia Commons，各图片的授权以原页面为准。
