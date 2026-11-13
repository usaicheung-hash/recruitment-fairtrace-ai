# Recruitment FairTrace AI：一步一步使用指南

打開 demo：**https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai**

所有 CV 同數據都係合成嘅。每一頁打開就係一次已儲存嘅真實運行，所以唔使密碼、唔使用 AI 額度都睇得到。
（English version: [USER_GUIDE_EN.md](USER_GUIDE_EN.md)）

---

## 0. 開始之前：認識個畫面

![Header](img/00_header.png)

1. **頁頂**：FairTrace 嘅五個步驟：① Rubric → ② Blind → ③ Score → ④ Audit → ⑤ Trace。
2. **Owner controls**：只係 owner 用嚟即場行 AI，一般用家唔使理。
3. **分頁**：由左去右睇：*Fair Rubric → Blind & Score → FairTrace Auditor → Decision Trace → Model choice →
   Summary*。*About & Ethics* 講用咗咩 model 同限制。

**顏色代表咩（每頁都一樣）**

| 顏色 | 意思 |
|---|---|
| 🟠 橙色 | **naive AI**（只係一句 prompt：「幫呢份 CV 打 0–100 分」），即係好多公司而家用緊嘅做法 |
| 🟣 紫色 | **FairTrace** |
| 🔴 紅色 | 偏見或者風險 |
| 🟢 綠色 | 已修正、公平、已批准 |

見到 ▶ 嘅位（例如 *How it works*、*Show raw*）都可以撳開睇多啲細節。

---

## 第 1 步：① Fair Rubric，檢查 job ad

![Job ad review](img/01_rubric_review.png)

1. 左上：**Risky phrases found**，即係搵到幾多句有風險嘅字眼，同埋係邊類風險（🎂 年齡、👶 家庭、🌏 種族或國籍）。
2. 左邊卡：**HR 寫嘅 job ad**，紅色字就係有風險嘅字眼（例如「young and energetic」、「no career gaps」、
   「native English speaker」）。
3. 右邊卡：**AI suggestions**。每一行有：被劃走嘅字眼、涉及嘅受保護特徵同香港條例，同埋綠色嘅建議寫法。
4. 留意黃色標籤 **⚠ still risky: HR must edit**：固定詞表再檢查 AI 自己嘅建議，發現仲有「2020 or later」
   （年齡字眼）。呢度示範到點解一定要人手覆核 AI。
5. 撳 **▶ Why each phrase is risky**，睇每句點解有風險。
6. 撳紫色掣 **✅ HR accepts the rewrite → build the rubric**。

![Rubric](img/02_rubric_approved.png)

7. 彩色條就係**評分準則（rubric）**：5 個同工作有關嘅評分項同比重，下面寫住咩證據先拎到分。
   年齡、性別、家庭狀況、國籍、殘疾、名、career gap 一律唔計分。

---

## 第 2 步：② Blind & Score，比較兩個篩選器

![Key numbers](img/03b_score_kpis.png)

1. 先睇頂部 4 個數字（橙色 = naive AI → 紫色 = FairTrace）：
   - **Score spread**：5 份資歷一樣嘅 CV，最高同最低分相差幾多（越低越公平）。
   - **Qualified people wrongly cut**：有幾多個合資格嘅人被錯誤刷出 shortlist。
   - **Points backed by a verified quote**：有幾多分有 CV 原文證據，同埋 Python 捉到幾多句有問題嘅引文。
   - **Cost per CV**：每份 CV 成本。

![Score spread](img/03_score_spread.png)

2. **點圖**：每粒點代表一個資歷一樣嘅申請人（A1–A5）。公平嘅篩選器會將佢哋放喺同一個位。
   橙色範圍（naive AI）明顯闊過紫色範圍（FairTrace）。

![All applicants](img/04_score_all.png)

3. **All 6 applicants**：橙色 bar = naive AI，紫色 bar = FairTrace，旁邊寫住 *shortlisted*（入選）定 *cut*（刷走）。
   A6 經驗真係少啲，所以兩個篩選器都應該畀佢低分。
4. 喺圖下面嘅 **Open an applicant** 揀一個人（預設係 A2，有 2 年 parental break）。

![Original vs blind CV](img/05_applicant_blind.png)

5. 左邊係**原本嘅 CV**，紅色劃線嘅字喺評分前已經被移走（名、email、畢業年份、career break、殘疾線索）。
   右邊係 **FairTrace 評分時見到嘅版本**，綠色標籤係被取代咗嘅位置。

![Evidence](img/06_applicant_evidence.png)

6. **FairTrace score**：每個評分項嘅分數（滿分 5）同 AI 引用嘅 CV 原文。Python 會檢查每句引文係咪真係喺 CV 入面，
   搵唔到就 0 分。
7. 最底係 **Naive AI 嘅理由**。A2 嘅例子入面，naive AI 話 career break「may affect recent industry knowledge」，
   呢個就係偏見。
8. （只限 owner）**Try your own CV**：貼一份合成 CV 即場評分。

---

## 第 3 步：③ FairTrace Auditor，睇 AI agent 審計篩選器

1. 撳 **▶ Replay saved audit**，agent 會逐步做嘢（大約 10 秒）。

![Agent timeline](img/07_audit_timeline.png)

2. 每一步顯示：用咗咩工具（🧪 測試、🔍 翻查理由、🛠 試修正、🏁 完成）、結果，同埋標籤：
   **BIAS**（紅）、**⚠ POSSIBLE BIAS**（黃）或者 **no bias**（綠）。灰色字講 agent 點解揀呢一步，
   同埋係 *AI planner* 定係固定 *rule* 揀嘅。

![Audit result](img/08_audit_attribute.png)

3. Timeline 下面，每個個人特徵（名、年齡、career break、殘疾）一張卡，三欄用同一個刻度：
   **Before（naive AI）**、**+ fairness rule in prompt**、**FairTrace pipeline**。紅色 bar = 得分最低嗰份。
   每欄下面嘅 *gap* 係最高同最低分嘅差距。
4. 如果 agent 翻查咗理由，會見到 AI 原句，相關字眼會標黃；或者寫住 AI 從來冇提過（即係隱藏偏見）。
5. 撳 **▶ How the verdict is decided**：BIAS = 差距 ≥ 3 分而且大過雜訊兩倍；POSSIBLE BIAS = 差距 ≥ 3 分但未夠雜訊兩倍。
6. 撳 **✅ Approve recommended fix**（或者 **❌ Reject**）。

![Human approval](img/09_audit_approved.png)

7. 綠色橫幅確認咗人手決定，同時會出現 **Audit report (Markdown)** 俾你下載。

---

## 第 4 步：④ Decision Trace，翻查任何一個決定

![Trace numbers](img/10_trace_kpis.png)

1. 揀一個申請人，頂部顯示記錄咗幾多次 AI call、用咗幾多 token、成本同時間。

![Letter](img/11_trace_letter.png)

2. **Explanation for the applicant**：AI 根據評分結果起草嘅解釋信，要招聘人員睇過先會發出。
3. **Calls by component**：每個部分 call 咗幾多次（naive AI、Blind Parser、Evidence Scorer、Letter writer）。

![One call](img/12_trace_call.png)

4. **Every call, in order**：時間、組件、model、temperature、用咗幾耐、AI 答案嘅易讀摘要同成本。
   撳 **▶ Show raw** 睇 AI 原文、prompt 版本同輸入 hash。
5. 撳 **⬇ Download the full Decision Trace (JSONL)** 下載全部記錄。

---

## 第 5 步：📊 Model choice，點解揀呢啲 model

![Model choice](img/13_model_choice.png)

1. 橙色 bar：用 naive prompt 嘅不公平差距，三個 model 都有差距。
2. 紫色 bar：用 FairTrace 方法之後嘅差距，揀咗嗰個 model 差距最細。
3. 撳 **▶ Show all numbers** 睇每次跑嘅分數穩定度、separation（仲分唔分得出強同弱嘅 CV）、證據、每份 CV 成本同時間。

---

## 第 6 步：🏁 Summary，一頁睇晒成個測試

![Summary numbers](img/14_summary_kpis.png)
![Summary charts](img/14b_summary_charts.png)
![Scorecard](img/14c_summary_scorecard.png)

1. 5 個重點數字：分數差距、錯誤刷走、證據、偏見標記、成本。
2. 左圖：每個申請人同參考 CV A1 嘅分數差距，公平 = 貼住 0 線。
3. 右圖：每個個人特徵喺修正前後嘅偏見差距。
4. **Naive AI vs FairTrace** 對比表、對公司嘅 3 個好處、學到嘅嘢。簡報收尾可以用呢頁。

---

## 7 分鐘講稿建議（Proposed GenAI Solution）

| 時間 | 講咩 | 畫面 |
|---|---|---|
| 0:00–1:00 | 由問題接落嚟：naive AI 對資歷一樣嘅 CV 因為 career break／年齡扣分。介紹五個步驟 | 頁頂 header |
| 1:00–2:30 | GenAI 技術、model 選擇（三個 model 用 naive prompt 都有差距，方法比 model 重要）、數據全部合成、點解唔 fine-tune | 📊 Model choice + About |
| 2:30–3:15 | ① Fair Rubric：紅字、AI 建議、「still risky」標籤、撳 accept | ① |
| 3:15–4:30 | ② Blind & Score：頂部數字、點圖、打開 A2 睇被移走嘅資料同證據 | ② |
| 4:30–5:45 | ③ Auditor：撳 replay，講 agent 每一步，最後撳 Approve | ③ |
| 5:45–6:30 | ④ Decision Trace：解釋信、記錄、Show raw、下載 | ④ |
| 6:30–7:00 | 🏁 Summary 收尾：「唔止快，仲可以證明公平」，交俾 Results 段落 | 🏁 |

---

## Owner：開 live 模式

![Owner controls](img/15_owner_controls.png)

1. 喺 Space 嘅 **Settings → Variables and secrets** 加兩個 **secret**（唔好揀 variable）：`HF_TOKEN`（有
   *Make calls to Inference Providers* 權限嘅 Hugging Face token）同 `APP_PASSWORD`（自己諗一個密碼）。
2. 打開 **🔒 Owner controls**，輸入密碼，就可以用 **🔄 Run live audit**（大約 3 分鐘、大約 US$0.02）或者
   **Try your own CV**。
3. Live 結果每次都會少少唔同，AI model 係會咁。簡報建議用 **Replay**。

喺自己部電腦更新已儲存嘅結果：`HF_TOKEN=... python build_cache.py`，再 `python benchmark.py`。

## 限制

合成數據嘅示範原型：一個職位、6 個申請人、每份 CV 跑 3 至 5 次。唔係科學或者法律審計。
唔好用嚟搵「最高分嘅名」或者教人點樣改 CV 嚟呃過篩選器。
