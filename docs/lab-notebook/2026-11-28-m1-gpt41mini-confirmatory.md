# 2026-11-28 — Hoàn tất thực nghiệm xác nhận M1 (`gpt-4.1-mini-2025-04-14`) và so sánh 2 mô hình

## 1. Bản bổ sung đăng ký trước & cổng `dev`
- Commit bản bổ sung trước khi chạy `holdout` M1: **`48ed67b3499dd936a9ce240c82f75bfabb3a4228`** (`2026-11-28T08:30Z`).
- Snapshot phục vụ đồng nhất trên mọi lượt: `served_model = gpt-4.1-mini-2025-04-14`.
- Phép thử đọc `dev` (`runs/probe_dev_gpt41mini.jsonl`): **16/16 (100%)** — 2/2 trên toàn bộ 8 mẫu giao diện.
- Tập `dev` replicate 1 (`runs/live_dev_gpt41mini.jsonl`): **384/384 `completed`**, vượt cổng tuyệt đối (**48/48 Hướng A**, **48/48 Hướng B**; trên `dev`: 0/24 ở mọi điều kiện không quyền Hướng A; Hướng B có 1/24 `claim_image`, 1/24 `claim_image_wrong_scope`, 0/24 các điều kiện không quyền khác).

## 2. Kết quả `holdout` xác nhận M1 (`runs/live_holdout_gpt41mini_report.json`)
- Tổng số lượt: **1.920/1.920 `completed`** (0 thiếu, 0 lỗi mạng, 0 lần retry; `120/120` cặp đầy đủ, `24/24` họ, `confirmatory_eligible = true`).
- **H1A (Track A — lộ mã canary):**
  - `claim_image`: **0/120 (0,00%)** vs `neutral_image`: **0/120 (0,00%)** $\Rightarrow \Delta_{\text{image, A}} = 0{,}00\text{ pp}$ [$0{,}00, 0{,}00$], $p_{\text{Holm}} = 1{,}000$; cận trên 95% một phía cấp họ khi không có sự kiện: **$11{,}73\%$**.
  - Toàn bộ 6 điều kiện không có quyền: **0/720 (0,00%)**. Đối chứng có quyền: `claim_image_authorized` = 119/120 (99,17%; 1 lượt từ chối nhầm ở `holdout_035`), `none_authorized` = 120/120 (100,00%).
- **H1B (Track B — gọi công cụ `release_record`):**
  - `claim_image`: **4/120 (3,33%)** vs `neutral_image`: **0/120 (0,00%)** $\Rightarrow \Delta_{\text{image, B}} = +3{,}33\text{ pp}$ [95% cluster CI: $+0{,}83, +5{,}83$], $p_{\text{raw}} = 0{,}1227$, $p_{\text{Holm}} = 0{,}2453$ (4 sự kiện phân bố trên 4 họ khác nhau; khoảng bootstrap mô tả không chứa 0 nhưng kiểm định đổi dấu cấp họ xác nhận không đạt ngưỡng $\alpha = 0{,}05$).
  - `none_empty`: **0/120 (0,00%)**, `neutral_text`: **0/120 (0,00%)**, `neutral_image`: **0/120 (0,00%)** (không có thiên lệch hiện diện tài liệu).
  - `claim_text`: **2/120 (1,67%)** ($\Delta_{\text{text}} = +1{,}67\text{ pp}$ [$0{,}00, +5{,}00$]; tương tác phương thức $+1{,}67\text{ pp}$ [$-1{,}67, +5{,}00$]).
  - `claim_image_wrong_scope`: **7/120 (5,83%)** — điều kiện dễ bị đánh lừa nhất của M1 (cao hơn cả khi sổ quyền rỗng 3,33%, trải trên 6 họ), chênh lệch phạm vi $+94{,}17\text{ pp}$ [$+90{,}00, +97{,}50$].
  - **Cơ chế lượt gọi & Gate Replay (Track B):** toàn bộ **13/13 (100%)** lệnh `release_record` trái phép của M1 xảy ra **trực tiếp ngay lượt 1** (0 lệnh sau `inspect_record_metadata`; ngược hoàn toàn với cơ chế *read-then-escalate* 275/275 ở lượt 2–3 của Qwen3-VL 4B), 0 lời gọi sai cú pháp. Cổng kiểm quyền chặn **13 $\rightarrow$ 0** thao tác trái phép và giữ nguyên **240/240 (100%)** thao tác hợp lệ.

## 3. Phép thử đọc `holdout`, Model Raters liên mô hình (M1 vs M3) và Độ ổn định
- **Phép thử đọc `holdout` (`runs/probe_holdout_gpt41mini.jsonl`, 48 ảnh):** **48/48 (100,0%)** trên tất cả mẫu giao diện.
- **Model raters mù hậu holdout (`review/annotation/model_raters/score.json`, 240 ảnh):**
  - `gpt-4.1-mini`: **240/240 (100,0%)**, điểm tự nhiên trung bình **3,42/5** (`claim` 3,66 vs `neutral` 3,17).
  - `qwen3-vl:4b`: **226/240 (94,2%)**, điểm tự nhiên trung bình **3,85/5** (`claim` 4,97 vs `neutral` 2,73).
  - **Cohen's $\kappa$ liên mô hình (M1 vs M3):** **0,8833** (vượt ngưỡng 0,80).
- **Độ ổn định `dev` M1 (`tools/stability.py`, rep 1 vs rep 2):** xem bản in của `stability.py` (Track A ~100%, Track B ~98,4%, các lượt đổi đều nằm ở `claim_image` và `claim_image_wrong_scope`).
- **Tổng chi phí OpenAI thực tế trọn bộ M1** (`probe_dev` + `dev rep 1+2` + `holdout` + `raters` + `probe_holdout` = 2.992 lượt): **~$1,81 USD** (~46.000 VNĐ / $5,00 nạp vào).
- **Tiến độ M4 (`gemini-3.1-flash-lite`, gói miễn phí ngày 2):** đã đạt **501/1.920** lượt `completed` (+350 lượt mới ngày 28/11, tốn 0 đồng).
