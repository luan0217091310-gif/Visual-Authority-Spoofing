# Referee report R2 — VAS
Reviewed: `paper/main.tex` @ 2026-11-26 (sau sửa R1) · Target: CORE A (ứng viên ESORICS, LNCS) · Contribution type: Benchmark / dataset (rubric đóng băng từ R1)
Independence: **same-context self-check** — cùng phiên vừa sửa bài; điểm này cần được xác nhận bằng phản biện ở phiên mới · Evidence accessed: như R1 + `tools/annotation.py`, `tools/stability.py`, thử nghiệm bảng nhiều mô hình bằng báo cáo giả (đã xóa)

## 1. Verdict
**MAJOR REVISION** — các lỗi viết, định vị và thiết kế phụ đã sửa; điều kiện chặn hạng A vẫn là chưa có kết quả mô hình (I-001).

## 2. Overall score
**6.5 / 10** (trước cap 6.9; cap 6.5 vì I-001 còn mở) · Confidence 4.
Tier gate A 8.0: không đạt, thiếu 1.5.

## 3. Contribution summary
Như R1; thêm: đăng ký nhóm mô hình, MDE, kiểm tra ổn định, quy trình chấm người đọc, định vị so với MMA-SafetyBench/DIBench.

## 4. Strongest reasons to reject
1. Chưa có ước lượng trên mô hình (I-001).
2. Nhóm mô hình mới đăng ký khung, chưa có tên mô hình 2–4 (I-002).
3. MDE 16 điểm với n = 120: hiệu ứng nhỏ hơn sẽ không phân biệt được với 0 (I-003).
4. Chưa có kết quả chấm người đọc (I-005).

## 5. Scores by criterion
| Dimension | Weight | R1 | R2 | Driving issues |
|---|---|---|---|---|
| Novelty | 1.5 | 0.83 | 1.05 (0.70) | I-004 resolved |
| Soundness | 1.5 | 1.05 | 1.28 (0.85) | I-006, I-007, I-009 resolved |
| Rigor | 1.5 | 0.60 | 0.68 (0.45) | I-001 open; I-002, I-003 partial |
| Data quality | 2.0 | 1.40 | 1.50 (0.75) | I-010 resolved; I-005 partial |
| Significance | 1.5 | 0.60 | 0.60 (0.40) | I-001 |
| Clarity | 0.75 | 0.64 | 0.64 (0.85) | — |
| Reproducibility | 1.0 | 0.85 | 0.90 (0.90) | I-008 resolved; open-model backend |
| Ethics | 0.25 | 0.21 | 0.25 (1.00) | I-011 resolved |
Total before caps 6.9 → after caps **6.5**.

## 8. Roadmap để vượt gate A (ước lượng nội bộ, không phải xác suất được nhận)
| Bước | Việc | Ai | Ảnh hưởng dự kiến lên điểm |
|---|---|---|---|
| 1 | Chấm người đọc 240 ảnh, báo cáo κ | tác giả (miễn phí) | Data quality → ~0.85 |
| 2 | Chốt nhóm mô hình + cỡ holdout, khóa prereg | tác giả | Rigor ↑ |
| 3 | Chạy dev ×2, probe, holdout cho ≥ 3 mô hình | tác giả + API | gỡ cap; Rigor, Significance ↑ |
| 4 | Viết Results/Discussion theo số thật, thêm hình tỉ lệ theo điều kiện × mô hình | writer | Clarity, Significance |
| 5 | Phản biện độc lập ở phiên mới (`/paper-referee`) | — | xác nhận điểm |

Nếu bước 3 cho kết quả rõ (hiệu ứng khác 0 ở ít nhất một mô hình, probe ≥ 90%, cổng chặn mọi ghi trái phép) hoặc một kết quả âm tính chặt (khoảng tin cậy hẹp quanh 0 với probe đạt), ước lượng nội bộ có thể lên khoảng 7.5–8.0. Đây là ước lượng có điều kiện, không phải cam kết.

## 10. Change log
Xem bảng “Trạng thái sau R2” trong `ISSUES.md`.

### Correct controls
- Bảng 4 sinh đúng một hàng mỗi mô hình (thử với báo cáo giả, đã xóa; sau khi xóa bảng quay lại `[pending]`).
- MDE tính bằng chia đôi trên cùng công thức power; khớp power 36%/75%.
- 20 tài liệu tham khảo, 20 được trích; các mục mới đã kiểm qua arXiv/Crossref.
- 16/16 unit test đạt.

### Not checked
- Biên dịch LNCS (không có TeX); chạy mô hình (không có khóa API); `codespell`.
