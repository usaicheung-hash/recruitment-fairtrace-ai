# Recruitment FairTrace AI 使用指南

Live demo：https://huggingface.co/spaces/edwardwww/recruitment-fairtrace-ai
所有 CV 同數據都係合成嘅。每一頁打開就係一次已儲存嘅真實運行，唔使額度都用得到。

## 一句講晒

Rubric → Blind → Trace → Audit：AI 幫 HR 快速篩 CV，但係每一分都要有 CV 原文做證據、個人資料先遮走、
每次 AI call 都有記錄，仲有一個 AI agent 不斷測試個篩選器有冇偏見。重要步驟一定由人批准。

## ① Fair Rubric（公平評分準則）

1. 睇 HR 寫嘅 job ad，紅色字係有風險嘅字眼（「young and energetic」、「no career gaps」、「native English speaker」）。
2. 表格逐句解釋：涉及咩受保護特徵、點解有風險、建議點改、對應香港咩條例。
3. 撳 **✅ HR accepts the rewrite → build the rubric**，就會見到改好嘅 job ad 同 5 個同工作有關嘅評分項（有比重）。之後每份 CV 都用呢套準則評分。

## ② Blind & Score（遮名 + 有證據評分）

1. 最頂一行係重點數字：5 份資歷一樣嘅 CV 分數相差幾多（naive AI 對比 FairTrace）、有幾多分有驗證過嘅證據、每份 CV 成本同時間。
2. 表格：同一批 6 個申請人，兩種篩選器嘅分數。A1–A5 資歷完全一樣，只係改咗一樣個人資料；A6 經驗真係少啲。
3. 喺下拉選單揀一個申請人：左邊係原本 CV（劃咗線嘅係被遮走嘅資料），右邊係 FairTrace 評分時見到嘅版本；下面每個評分項都有 AI 引用嘅原文，同埋 Python 有冇喺 CV 搵到嗰句（搵唔到就 0 分）；最底係 naive AI 嘅分數同理由。
4. **Try your own CV**（要 owner 密碼）：貼一份合成 CV 即場評分。

## ③ FairTrace Auditor（AI 審計 agent）

1. 撳 **▶ Replay saved audit**。Agent 逐步做嘢：用對照 CV 測試名、年齡、career break、殘疾；搵到差距就翻查 AI 嘅理由；試修正再重測。
2. 每一步顯示用咗咩工具、點解、係 AI planner 揀定係規則後備揀。
3. 結果表：差距、雜訊、判斷（由統計計：差距 ≥ 3 分而且大過雜訊兩倍）、修正後差距。
4. 撳 **✅ Approve** 或 **❌ Reject**：決定會被記錄，可以下載 Markdown audit report。
5. **Run live audit**（要 owner 密碼）：用真 model 再跑一次（大約 3 分鐘）。

## ④ Decision Trace（決策記錄）

揀一個申請人，睇到佢每一次 AI call 嘅記錄（時間、組件、model、temperature、prompt 版本、輸入 hash、AI 原文、tokens、秒數），
同埋 AI 起草嘅解釋信。可以下載完整記錄（JSONL）。

## 📊 Model choice（model 選擇）

3 個 model × 2 種方法，同一批申請人。Spread 同 SD 越低越公平、越穩定；separation 越高代表仍然分得出強同弱嘅 CV。已選用嘅組合會highlight。

## 7 分鐘講稿建議（Proposed GenAI Solution）

| 時間 | 講咩 | 畫面 |
|---|---|---|
| 0:00–1:00 | 由問題接落嚟：naive AI 對同一份 CV 因為 career break／年齡扣分。介紹 Rubric → Blind → Trace → Audit | 流程圖 slide |
| 1:00–2:30 | GenAI 技術、model 選擇（📊 Model choice 表：三個 model 用 naive prompt 都有 5 分差距，FairTrace + Qwen3-235B 差距 0）、數據全部合成、點解唔 fine-tune | 📊 tab + slide |
| 2:30–3:15 | ① Fair Rubric：紅字、表格、撳 accept | ① tab |
| 3:15–4:30 | ② Blind & Score：頂部數字、表格、打開 A4 或 A2 睇遮走咗咩同證據 | ② tab |
| 4:30–5:45 | ③ Auditor：撳 replay，講 agent 每一步，最後撳 Approve | ③ tab |
| 5:45–6:30 | ④ Decision Trace：解釋信 + 記錄 + 下載 | ④ tab |
| 6:30–7:00 | 收尾：「唔止快，仲可以證明公平」，交俾 Results 段落 | — |

## Owner：開 live 模式

喺 Space settings 加兩個 secret：`HF_TOKEN`（可以 call Inference Providers 嘅 Hugging Face token）同 `APP_PASSWORD`。
喺頁頂輸入密碼就用到 live 掣。本機更新 cache：`HF_TOKEN=... python build_cache.py` 同 `python benchmark.py`。

## 限制

合成數據嘅示範原型：一個職位、6 個申請人、每份 CV 跑幾次。AI 每次答案會有少少唔同，所以 FairTrace 會量度雜訊同持續審計。唔係科學或法律審計。
