# D — Dữ liệu / Đánh giá / Ca lỗi / Báo cáo & Slide

Đọc README, CONTRACTS, MERGE. Sở hữu evaluate.py, tests/test_evaluate.py, evidence/, docs/report.md, slides/. D soạn fixtures mới; C điều phối merge vì B/C dùng chung.

## 10–65 phút: không chờ live

- [ ] Tạo fixtures dài với timestep 0,2 s và expected outcomes cho association/crossing/return/occlusion/gap/ID switch.
- [ ] Viết scorer/tests: alert type riêng reminder; match một-một 5–8 s, duplicate, early/late, positive không match, mẫu số 0.
- [ ] Fixture TP=1, FP=1, FN=1 phải cho precision/recall=0,5. Nhãn không chứa prediction.
- [ ] Chuẩn bị 7 cảnh, đồng ý ghi hình, labels CSV đúng schema; khung report/8 slide từ đầu.

## 65–125 phút: thu và chấm thật

4 calibration riêng; sau khóa config tối thiểu 2 lần/cảnh nếu kịp:

| Mã | Tình huống | Kỳ vọng |
|---|---|---|
| T01 | Ngồi cạnh balô | Không alert |
| T02 | Rời vùng, để balô | Reminder crossing; alert trong 5–8 s |
| T03 | Quay lại trước 5 s | Không alert; reminder có thể đã phát |
| T04 | Cầm balô đi | Không reminder/alert khi đủ quan sát mang theo |
| T05 | Người còn đó nhưng bị che | UNCERTAIN, không tự suy ra exit |
| T06 | Balô nằm sẵn, chưa liên hệ | Không alert |
| T07 | Người khác đi ngang | Không đổi người liên quan |

- [ ] Gán nhãn độc lập theo video+timestamp sidecar; không lấy detector làm chân lý. Báo số mẫu thực, không âm thầm loại ca khó.
- [ ] Tăng T02 nếu kịp vì hai positive quá ít; không suy rộng 14 phiên tự diễn thành chất lượng thư viện thật.
- [ ] Metric: TP/FP/FN/n, precision/recall, delay_total, processing p50/p95, thời gian UNCERTAIN; reminder delay chấm riêng.
- [ ] Baseline mất-detection-thì-báo và candidate crossing+UNCERTAIN dùng cùng log. Lỗi baseline không được gọi là lỗi candidate.
- [ ] Tìm một lỗi candidate thực: mất ID tại crossing, balô bị che gây FN, hoặc false association. Giữ video/log/nhãn/lý do; không tạo event giả.

## 125–180 phút: tài liệu và trình bày

Điền report từ evidence cùng run/config hash; lấy phần model của A, logic của B, ảnh/runbook của C. Tạo PPTX/PDF bằng skill presentations khi thực hiện, render kiểm tra. Số 83,3% trong tài liệu tham khảo không phải kết quả nhóm.

Tests/scorer phải có CLI hoặc lệnh Python chạy lại được, chưa có ở scaffold. Bàn giao metrics/per_event/results, n, lỗi thực, report/deck và phần chưa chứng minh. Không commit raw media mặc định.
