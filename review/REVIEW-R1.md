# Referee report R1 — VAS
Reviewed: `paper/main.tex` @ 2026-11-26 (working tree, chưa commit) · Target: CORE A (ứng viên định dạng LNCS: ESORICS — CORE A theo myhuiban/PaperPilot; nhà xuất bản LNCS chưa xác minh) · Contribution type: Benchmark / dataset kèm giao thức đăng ký trước
Independence: **same-context self-check** (cùng phiên đã viết bài; không phải phản biện độc lập) · Evidence accessed: `data/*/manifest.jsonl`, ảnh, `runs/*`, `paper/generated/numbers.json`, code, metadata arXiv/Crossref · Assumptions: không có log mô hình thật; mục tiêu A (gate 8.0).

## 1. Verdict
**MAJOR REVISION** — thiết kế và kiểm định kích thích chặt chẽ, nhưng câu hỏi trung tâm (một tuyên bố phê duyệt làm thay đổi quyết định bao nhiêu) chưa có bất kỳ ước lượng nào trên mô hình thật, nên ở hạng A bài chưa có đóng góp thực nghiệm.

## 2. Overall score
**6.2 / 10** (cap: ≤ 6.5 vì I-001; ≤ 7.0 vì ≥ 3 MAJOR mở) · Confidence 4: đã kiểm lại số liệu, ảnh, trích dẫn qua API; chưa có log mô hình để kiểm phần kết quả.
Tier gate A 8.0: **không đạt**, thiếu 1.8 · Author default gate 8.0: thiếu 1.8.

## 3. Contribution summary
Bài hỏi: khi sổ cấp quyền từ chối, đổi một câu trạng thái từ “đang chờ duyệt” sang “đã duyệt” làm tăng bao nhiêu tỉ lệ mô hình lộ canary (Track A) hoặc đề xuất gọi `release_record` (Track B). Đóng góp: 144 cặp ảnh tiếng Việt khác nhau chỉ trong vùng trạng thái, bộ chạy 8 điều kiện × 2 hướng có phát lại cổng kiểm quyền, và kế hoạch phân tích đăng ký trước. Bằng chứng hiện có là kiểm định kích thích và phần mềm; chưa có kết quả mô hình.

## 4. Strongest reasons to reject
1. Không có kết quả mô hình nào; ở hạng A, benchmark không kèm đánh giá trên các mô hình hiện hành thường bị coi là chưa hoàn chỉnh (I-001).
2. Chỉ một snapshot được đăng ký làm phân tích xác nhận; kết luận không thể tổng quát cho “multimodal models” (I-002).
3. Độ mạnh dự kiến thấp (36% cho hiệu ứng 10 điểm), nên kết quả âm tính sẽ khó diễn giải (I-003).
4. Thiếu các công trình gần nhất công bố 9–11/2026 (MMA-SafetyBench, DIBench, Repeat-After-Me) và các phòng thủ theo hướng thiết kế (CaMeL); vị trí đóng góp chưa được chứng minh đầy đủ (I-004).
5. Chưa có kiểm định của người đọc rằng câu “đã duyệt” thật sự được hiểu là phê duyệt và tự nhiên với người Việt (I-005).

## 5. Scores by criterion (frozen rubric: Benchmark / dataset)
| Dimension | Weight | Score | Driving issues | Reason |
|---|---|---|---|---|
| Novelty and originality | 1.5 | 0.83 (0.55) | I-004 | Thiết kế cặp tối thiểu + sổ quyền độc lập là mới so với các bài đã trích, nhưng thiếu so sánh với các bài gần nhất 2026 |
| Technical soundness | 1.5 | 1.05 (0.70) | I-006, I-007, I-009 | Estimand, ghép cặp, cụm theo họ đúng; tương phản là “đã duyệt” vs “chưa được cấp quyền” (có câu từ chối tường minh); bootstrap percentile với 24 cụm có thể hụt độ phủ |
| Experimental rigor | 1.5 | 0.60 (0.40) | I-001, I-002, I-003 | Chưa chạy mô hình; một snapshot; power thấp |
| Data and label quality | 2.0 | 1.40 (0.70) | I-005, I-010 | Kiểm định điểm ảnh rất chặt; thiếu kiểm định người đọc; holdout lệch mẫu giao diện |
| Significance | 1.5 | 0.60 (0.40) | I-001 | Chưa có phát hiện về hành vi mô hình |
| Clarity and writing | 0.75 | 0.64 (0.85) | L-001… | Rõ, câu ngắn; vài chỗ cần chính xác hơn |
| Reproducibility | 1.0 | 0.85 (0.85) | I-008 | Mã băm, seed, môi trường render, log; thiếu nói về tính không tất định của API |
| Limitations, ethics | 0.25 | 0.21 (0.85) | I-011 | Đầy đủ; thiếu câu về phê duyệt đạo đức (không có người tham gia) |
Total before caps: 6.18 → after caps: **6.2** (cap 6.5 không ràng buộc).
Consistency check: có.

## 6. Claim ledger
| C-ID | Quote (location) | Evidence at claimed scope | Verdict |
|---|---|---|---|
| C1 | “pixel-identical outside a fixed region” (abstract) | `verify_paired_images`, numbers.json `pairs_inside_box` 144/144 | supported |
| C2 | “differ by a median of 7 word edits” (§4) | numbers.json `edit_median` | supported |
| C3 | “renders repeat exactly on one machine” | `--check-determinism` → identical | supported |
| C4 | “the check blocks every unauthorized write in scripted replays” | fixture logs 88 / 0 | supported (scripted only, stated) |
| C5 | “Most of these attacks carry an instruction” (§1) | trích FigStep, VPI-Bench, MMPIBench… | partial — MMA-SafetyBench dùng cảnh báo giả mang ngữ nghĩa, cần nêu |
| C6 | “a paired, preregistered estimate of the claim's effect” (§2) | chưa có ước lượng | wording phải là “design for” (đã đúng ở chỗ khác) |

## 7. Defect register (this round)
Xem `ISSUES.md` (I-001 … I-011, L-001 … L-004).

## 8. Priority revision roadmap
1. **New experiment** — I-001, I-002: chạy dev + probe + holdout trên tối thiểu 3 mô hình (2 thương mại khác nhà cung cấp + 1 mô hình mở). Cần khóa API và ngân sách (quyết định của tác giả).
2. **Redesign nhỏ / quyết định** — I-003: mở rộng holdout (ví dụ 48 họ × 5 = 240 hồ sơ) trước khi khóa giao thức.
3. **Literature** — I-004: bổ sung và định vị so với MMA-SafetyBench, DIBench, Repeat-After-Me, CaMeL, persuasion/authority endorsement.
4. **Human validation** — I-005: hai người đọc tiếng Việt chấm mù cặp ảnh (đúng nhãn, tự nhiên); báo cáo kappa.
5. **Writing** — I-006…I-011, L-*.

## 9. Concrete rewrites and experiment plans
- **Thí nghiệm I-001/I-002:** giả thuyết H1A/H1B như đăng ký; mỗi mô hình một họ kiểm định Holm riêng, báo cáo mô hình là các nghiên cứu lặp lại, không gộp. Kết quả nào cũng được báo cáo; nếu Δ ≈ 0 với probe ≥ 90%, kết luận là “mô hình đọc được nhưng không coi tuyên bố là quyền” — một phát hiện có giá trị.
- **Kiểm định người đọc I-005:** 288 ảnh, thứ tự ngẫu nhiên, mù biến thể; hai người chấm “ảnh nói đã duyệt chưa?” và “câu có tự nhiên không (1–5)?”; đạt nếu độ chính xác ≥ 95% và κ ≥ 0.8.
- Rewrites: xem cột Replacement trong `ISSUES.md`.

## 10. Change log and next review gate
- **R1:** first review.
- **Next gate:** I-004, I-006…I-011 được sửa và kiểm; I-001/I-002 có kế hoạch được tác giả duyệt (khóa API, mô hình, ngân sách).

### Questions to authors
| ID | Question | Would change |
|---|---|---|
| Q1 | Có khóa API (OpenAI/Anthropic/Google) và ngân sách để chạy không? | I-001, I-002 → điểm Rigor, Significance |
| Q2 | Hội nghị đích cụ thể (ESORICS? ACL/EMNLP? khác)? | định dạng, giới hạn trang |
| Q3 | Có đồng ý mở rộng holdout trước khi khóa không? | I-003 |

### Not scored (suggestions)
- Biến thể sổ quyền nằm ngoài prompt (truy vấn qua công cụ) để tăng tính thực tế; cần nhiều lượt hội thoại nên để phiên bản sau.
- Biến thể “im lặng” (không có câu trạng thái) để tách hiệu ứng của câu từ chối tường minh ở bản neutral.

### Correct controls
- Mọi số trong bài truy về `numbers.json` (sinh bằng script), không có số gõ tay.
- 15/15 tài liệu tham khảo tồn tại; mô tả khớp abstract/bảng đã đọc.
- Track B tách đề xuất với thực thi bằng phát lại có/không cổng — đúng thiết kế.
- Analyzer từ chối log fixture khi `--confirmatory`.

### Not checked
- Không biên dịch được LNCS (máy không có TeX); kiểm bố cục trên bản xem trước HTML.
- Không chạy được mô hình (không có khóa API).
- `spell_check.py` cần `codespell`/`uv` — chưa chạy.
