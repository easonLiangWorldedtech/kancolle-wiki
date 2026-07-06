# KanColle Wiki — AI Research Engine

## 📊 Data Sources

### Official X Accounts (Changelog & Event Tracking)
| Account | Purpose | Frequency |
|---------|---------|-----------|
| **@KanColle_STAFF** | 官方更新、維護公告、活動預告 | 主要追蹤目標 |
| @C2_STAFF | 先行情報、合作活動、脫線資訊 | 次要追蹤 |

### Game Data Sources
- **KC3Kai Master:** `https://github.com/KC3Kai/KC3Kai` (ships.json, slotitem.json)
- **POI Store:** Real-time game state via POI plugin API

---

## 📁 Directory Structure

```
kancolle-wiki/
├── news/                    # X posts & changelogs
│   ├── 2026-07-kancolle-staff.md
│   └── ...
├── mechanics/               # HTML visual guides (AI-readable)
│   ├── combat-phases.html
│   ├── fleet-composition.html
│   └── resource-management.html
├── analysis/                # AI-generated insights
│   ├── ship-tier-list.md
│   └── meta-trends.md
└── raw-data/               # KC3Kai JSON dumps
    ├── ships.json
    └── slotitem.json
```

---

## 🤖 Cron Jobs

### 1. `kancolle-x-tracker` (Every 2 hours)
- **Source:** @KanColle_STAFF + @C2_STAFF
- **Trigger:** New tweets with keywords: 改修、イベント、メンテナンス、先行
- **Output:** `news/YYYY-MM-account.md`

### 2. `kancolle-data-sync` (Daily at 9am)
- **Source:** KC3Kai GitHub master branch
- **Action:** Sync ships.json + slotitem.json
- **Output:** `raw-data/` directory

### 3. `kancolle-meta-researcher` (Weekly on Sunday)
- **Source:** Community analysis, Reddit r/kancolle, Moegirl
- **Action:** Summarize current meta trends
- **Output:** `analysis/meta-trends.md`

---

## 🎯 AI Integration Points

### For Plugin UI:
1. Read `raw-data/ships.json` → Get accurate ship stats
2. Read `news/*.md` → Inject latest changelog into analysis
3. Read `mechanics/*.html` → Visual reference for combat phases

### For AI Analysis:
```javascript
// Example: AI reads wiki + POI data to generate recommendations
const ships = require('./raw-data/ships.json');
const news = fs.readdirSync('./news').map(f => readFileSync(`./news/${f}`));
const mechanics = fs.readFileSync('./mechanics/combat-phases.html', 'utf8');

// AI prompt: "Based on latest changelog + player fleet data, recommend..."
```

---

## 📋 Recent Updates (Auto-generated)

*This section will be populated by cron jobs.*
