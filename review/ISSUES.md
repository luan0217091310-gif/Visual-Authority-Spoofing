# Issue register — VAS — paper/main.tex

Frame (frozen in R1): target CORE A (ứng viên ESORICS, LNCS) · contribution type Benchmark / dataset · rubric weights [REVIEW-R1.md §5](REVIEW-R1.md)

| Round | Date | Reviewed version | Score | Verdict | Report |
|---|---|---|---|---|---|
| R1 | 2026-11-26 | paper/main.tex (working tree) | 6.2 | MAJOR REVISION | REVIEW-R1.md |
| R2 | 2026-11-26 | paper/main.tex (working tree, sau sửa R1) | 6.5 (cap) | MAJOR REVISION | REVIEW-R2.md |

## Trạng thái sau R2 (self-check cùng phiên; cần phản biện độc lập để xác nhận RESOLVED)

| ID | Trạng thái R2 | Ghi chú sửa (writer) / kiểm lại (referee) |
|---|---|---|
| I-001 | OPEN | Cần chạy mô hình thật; phụ thuộc khóa API và ngân sách (Q1). |
| I-002 | PARTIALLY FIXED | Bài và prereg đăng ký nhóm mô hình (≥2 thương mại + 1 mở), Holm riêng từng mô hình; thêm backend `chatcompat` cho mô hình mở; Table 4 sinh một hàng mỗi mô hình (đã thử bằng báo cáo giả rồi xóa). Còn thiếu: tên mô hình M2–M4 trong prereg. |
| I-003 | PARTIALLY FIXED | Bài nêu MDE 80%: 16 điểm (n=120), 11 điểm (n=240). Quyết định cỡ holdout chờ tác giả (Q3). |
| I-004 | FIX_CLAIMED → RESOLVED (self-check) | Thêm 5 nguồn đã kiểm qua arXiv/Crossref (MMA-SafetyBench, DIBench, Repeat-After-Me, CaMeL, Zeng et al. ACL 2024 — “Authority Endorsement” kiểm trong Table 1 của bài gốc); câu định vị so với MMA-SafetyBench ở §2. |
| I-005 | PARTIALLY FIXED | Chưa có người chấm. Thay tạm bằng hai mô hình chấm (`tools/model_raters.py`, chạy sau holdout xác nhận), ghi rõ là mô hình trong §4 và thêm vào Hạn chế (§8). Phiếu chấm người vẫn phát hành. |
| I-006 | RESOLVED (self-check) | §3 nêu rõ tương phản pending → approval và vai trò `none_empty`. |
| I-007 | RESOLVED (self-check) | §6: sign-flip là phép kiểm xác nhận, bootstrap mô tả, nêu giới hạn 6 họ/tầng. |
| I-008 | RESOLVED (self-check) | §5 “Stability”; `tools/stability.py`; prereg. |
| I-009 | RESOLVED (self-check) | Limitations nêu hướng sai lệch. |
| I-010 | RESOLVED (self-check) | §4 nêu cân bằng theo loại tài liệu, không theo mẫu; `analyze.py` thêm `exploratory_image_rates_by_template`. |
| I-011 | RESOLVED (self-check) | §9 thêm câu về người tham gia. |
| L-001 | RESOLVED | “a design for a paired, preregistered estimate”. |
| L-002 | RESOLVED | câu mới kèm trích dẫn. |
| L-003, L-004 | RESOLVED | cập nhật theo nhóm mô hình. |
| I-012 (mới, R2) · MINOR | OPEN | Bảng điều kiện có `egin{tabular}{lllll}` cho 4 cột — đã sửa thành `llll` trong cùng vòng; ghi lại để theo dõi. → RESOLVED |

## Issues

### I-001 · MAJOR · VERIFIED ERROR (missing evidence) · OPEN
- **Location:** §7 Table 4; abstract last sentence
- **Quote:** "This paper reports no model estimates"
- **Problem:** Câu hỏi nghiên cứu trung tâm chưa có ước lượng nào.
- **Why it matters:** ở hạng A, đóng góp chỉ còn bộ dữ liệu + giao thức; Significance và Rigor bị giới hạn.
- **Fix:** chạy dev → probe → holdout trên mô hình thật theo giao thức.
- **Acceptance test:** `runs/live_holdout_report*.json` có `report_mode = CONFIRMATORY_LIVE`; Table 4 không còn `[pending]`.
- **Author decision:** — · **Writer fix note:** — · **History:** R1 opened

### I-002 · MAJOR · WELL-SUPPORTED CONCERN · OPEN
- **Location:** §5 "Models and requests"; PREREGISTRATION §4
- **Problem:** chỉ một snapshot (gpt-4.1-mini) được đăng ký; không thể nói về “multimodal models” nói chung.
- **Fix:** đăng ký trước một nhóm mô hình (≥ 3, khác nhà cung cấp, có ít nhất một mô hình mở); mỗi mô hình là một lần lặp độc lập với Holm riêng cho H1A/H1B; pipeline sinh bảng theo từng mô hình.
- **Acceptance test:** prereg liệt kê nhóm mô hình trước khi khóa; `make_paper_numbers.py` sinh một hàng Table 4 cho mỗi báo cáo xác nhận.
- **History:** R1 opened; 2026-11-27: thêm kiểm tra bằng mô hình chấm, nêu rõ chưa có người đọc trong Hạn chế. Vẫn mở cho tới khi có người chấm thật.

### I-003 · MAJOR · VERIFIED ERROR (design) · OPEN
- **Location:** §6 "Planned power"
- **Quote:** "36% power for a 10-point effect"
- **Problem:** n = 120 hồ sơ / 24 họ cho power thấp; kết quả âm tính khó diễn giải.
- **Fix:** mở rộng holdout trước khi khóa (quyết định chi phí của tác giả), hoặc giữ nguyên và báo cáo khoảng tin cậy như kết quả chính, kèm ngưỡng hiệu ứng tối thiểu phát hiện được.
- **Acceptance test:** prereg ghi n cuối cùng và power tương ứng; bài nêu hiệu ứng tối thiểu phát hiện được (MDE).
- **History:** R1 opened

### I-004 · MAJOR · VERIFIED ERROR · OPEN
- **Location:** §2 Related Work
- **Problem:** thiếu MMA-SafetyBench (arXiv:2610.19384, cảnh báo giả có ngữ nghĩa kéo agent khỏi nhiệm vụ được phép), DIBench (2610.06898), Repeat-After-Me (2609.04533), CaMeL (2503.18813), và persuasion taxonomy có “Authority Endorsement” (Zeng et al., ACL 2024).
- **Fix:** thêm và nêu khác biệt: MMA-SafetyBench thay phần tử giao diện; VAS giữ nguyên giao diện, chỉ đổi một câu khẳng định, và điều khiển sổ quyền độc lập.
- **Acceptance test:** 5 mục mới có trong bibliography, đều đã kiểm qua arXiv/Crossref, mỗi mục được trích với một câu mô tả khớp abstract.
- **History:** R1 opened

### I-005 · MODERATE · MISSING INFORMATION · OPEN
- **Location:** §4 "Minimal pairs"; §7
- **Problem:** chưa có kiểm định người đọc rằng mỗi biến thể được hiểu đúng (đã duyệt / chưa) và tự nhiên.
- **Fix:** công cụ chấm mù cho hai người đọc tiếng Việt; báo cáo độ chính xác và Cohen's κ.
- **Acceptance test:** `tools/annotation.py` tạo phiếu chấm và tính độ chính xác, κ; bài có câu mô tả quy trình (và kết quả khi đã chấm).
- **History:** R1 opened

### I-006 · MODERATE · WELL-SUPPORTED CONCERN · OPEN
- **Location:** §3 "Spoofing", abstract
- **Problem:** bản neutral nói rõ “chưa được cấp quyền”, nên tương phản là phê duyệt vs từ chối/chờ, không phải phê duyệt vs không có thông tin. Đã nêu ở Limitations nhưng chưa nêu ở định nghĩa estimand.
- **Fix:** nói rõ ở §3 và §6 rằng Δ đo việc thay câu chờ duyệt (không cấp quyền) bằng câu phê duyệt; `none_empty` cho mốc không tài liệu.
- **Acceptance test:** câu trong §6 Estimand nêu đúng tương phản.
- **History:** R1 opened

### I-007 · MODERATE · WELL-SUPPORTED CONCERN · OPEN
- **Location:** §6 Inference
- **Problem:** bootstrap percentile với 24 cụm (6 mỗi tầng) có thể hụt độ phủ; bài không nói phép kiểm nào là chính khi hai cách mâu thuẫn.
- **Fix:** nêu rằng sign-flip là phép kiểm xác nhận, bootstrap là mô tả; ghi nhận giới hạn số cụm.
- **Acceptance test:** câu tương ứng có trong §6.
- **History:** R1 opened

### I-008 · MODERATE · WELL-SUPPORTED CONCERN · OPEN
- **Location:** §5
- **Problem:** API ở temperature 0 vẫn không tất định; bài chỉ dùng replicate 1 mà không nói độ ổn định.
- **Fix:** đăng ký replicate 2 trên dev làm kiểm tra ổn định (tỉ lệ đồng thuận theo lượt), không vào phân tích xác nhận.
- **Acceptance test:** §5 và prereg mô tả kiểm tra ổn định; analyzer/README có lệnh.
- **History:** R1 opened

### I-009 · MINOR · WELL-SUPPORTED CONCERN · OPEN
- **Location:** §3 "Parties and channels"
- **Problem:** sổ quyền nằm trong prompt, tức mô hình có “quy tắc đúng” trong tay; điều này làm thí nghiệm là cận dưới của rủi ro hay cận trên? Cần nói hướng sai lệch.
- **Fix:** thêm một câu: đặt sổ trong prompt là trường hợp thuận lợi cho mô hình, nên tỉ lệ lỗi đo được có thể thấp hơn hệ thống thật.
- **Acceptance test:** câu nêu hướng sai lệch có trong Limitations.
- **History:** R1 opened

### I-010 · MINOR · VERIFIED ERROR · OPEN
- **Location:** §4 Records and families, Table 1
- **Problem:** holdout không cân bằng mẫu giao diện (20/20/16/16/12/12/12/12) nhưng văn bản không nói, và không có kế hoạch báo cáo theo mẫu.
- **Fix:** nêu sự lệch và báo cáo tỉ lệ sự kiện theo mẫu giao diện như phân tích thăm dò.
- **Acceptance test:** câu nêu phân bố có trong §4; §6 có báo cáo theo template (thăm dò).
- **History:** R1 opened

### I-011 · MINOR · MISSING INFORMATION · OPEN
- **Location:** §9 Ethics
- **Problem:** không nêu tình trạng phê duyệt đạo đức.
- **Fix:** “The study involves no human participants or personal data, so no ethics-board approval was required; the planned annotation uses only the authors.” (điều chỉnh nếu có người chấm ngoài).
- **Acceptance test:** câu có trong §9.
- **History:** R1 opened

## Language table (MINOR unless promoted)
| ID | Location | Original | Problem | Replacement | Status |
|---|---|---|---|---|---|
| L-001 | §2 cuối | "a paired, preregistered estimate of the claim's effect" | chưa có ước lượng; nên nói thiết kế | "a design for a paired, preregistered estimate of the claim's effect" | OPEN |
| L-002 | §1 | "Most of these attacks carry an instruction." | “most” chưa được chống đỡ đầy đủ | "The attacks in these studies carry an instruction or redirect the agent to a new target." | OPEN |
| L-003 | §5 | "Adapters for the Gemini and Anthropic APIs are included for replication." | sau khi có nhóm mô hình, cần nhất quán | cập nhật theo I-002 | OPEN |
| L-004 | §7 | "Reporting." đoạn | cần nói rõ nhiều mô hình | cập nhật theo I-002 | OPEN |

## Questions to authors
| ID | Question | Would change |
|---|---|---|
| Q1 | Khóa API và ngân sách? | I-001, I-002 |
| Q2 | Hội nghị đích? | định dạng, trang |
| Q3 | Mở rộng holdout? | I-003 |

## Not scored (suggestions)
- Sổ quyền truy vấn qua công cụ (đa lượt).
- Biến thể không có câu trạng thái.
