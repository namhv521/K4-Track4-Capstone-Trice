# Plan đội 4 người — 180 phút

## Lịch song song

| Phút | A — CV | B — Engine | C — Integration | D — Evidence |
|---|---|---|---|---|
| 0–10 | Kiểm tra camera/model/balô | Chốt ROI/exit/timer | Chốt contract, máy demo | Đồng ý ghi hình, kịch bản/nhãn |
| 10–30 | infer/reset, box/ID thật | Tests + logic trên fixture | UI/recorder trên fixture | Fixtures/scorer/khung slide |
| 30–45 | Bàn giao observation thật | Ghép association/crossing | Ghép live toàn flow lần 1 | Kiểm tra log/timebase |
| 45–65 | Đo tốc độ/model card | Stationary/UNCERTAIN tests | Video/log/replay/kênh nhắc | Chấm thử, chuẩn bị cảnh |
| 65–80 | Thu calibration | Hiệu chỉnh, khóa config | Khóa timebase/ROI | Nhãn calibration riêng |
| 80–110 | Chạy máy test | Quan sát kỹ thuật, không tune | Đóng vai, kiểm tra recording | Gán nhãn độc lập, chấm test |
| 110–125 | Tái hiện lỗi, mô tả model | So baseline/candidate, debug | Sửa blocker/README | Metric, lỗi, counts/n |
| 125–160 | Rà model trên deck | Rà logic/trụ cột | Đóng gói, rà deck/replay | Report/PPTX/PDF |
| 160–180 | Vận hành máy | Giải thích state/bất định | Điều phối demo | Số đo/lỗi/giới hạn |

Checkpoint 10/30/45/65/80/125/160 phút. Mỗi lần merge chạy smoke và tests. Phút 45 phải nối được live; không để tới cuối mới tích hợp.

## Trụ cột và người chịu trách nhiệm

| Trụ cột | Nơi thực thi | Chủ trì | Evidence |
|---|---|---|---|
| 1 Học | YOLO person/backpack | A | Model card/hash/class mapping |
| 2 Hình học | ROI, box, normalize, crossing | B | Overlay/config; không đo mét |
| 3 Bất định | Measurement khác prediction, UNCERTAIN | A+B | Mất dấu/ID switch, ca sai |
| 4 Biểu diễn | Track/seat/association/state | B+C | JSONL và frame tương ứng |
| 5 Thời gian | Reminder crossing, alert 5 s, monotonic | C+B | Delay, p50/p95 processing |
| 6 Dữ liệu | Quality, session split, log/replay/nhãn | C+D | Video/manifest/ground truth |
| 7 Bằng chứng | Event score, baseline/candidate, gate | D | Counts/n, metric, lỗi thật |

Đào sâu biểu diễn thế giới và thời gian; dùng bất định/bằng chứng để bảo vệ kết luận.

## Liên hệ toàn Phase 2

- Lab 1–2: input/output, provenance, calibration/test, benchmark warmup/steady state; không train lại model không liên quan.
- Lab 3: detection, box, confidence; không cần segmentation/keypoint cho MVP.
- Lab 4: kiểm tra che khuất/ánh sáng có kiểm soát, không lấy log tổng hợp làm detector accuracy.
- Lab 5: prediction khác measurement; không gọi confidence YOLO là NIS.
- Lab 6: hệ tọa độ và giới hạn 2D; không tuyên bố LiDAR/calibration 3D đã triển khai.
- Lab 7–8: track lifecycle, association và mất dấu; không xác minh ownership hoặc fusion đa cảm biến từ một webcam.
- Lab 9–10: quality/schema, provenance/nhãn, split theo session; không cần Airflow/VLM online.
- Lab 11–12: stress kịch bản, replay, baseline/candidate và gate; không chứng minh điều khiển vòng kín vật lý.

## Nghiệm thu

Live thật dương/âm; reminder có ích tại chỗ; alert đúng timebase; UNCERTAIN đúng điều kiện; nhãn độc lập; metric có n; một lỗi candidate thực; log/replay; README/report/deck cùng run. Không đạt thì ghi rõ phần còn thiếu.

Cắt scope trước: UI web, nhiều vật/người/camera, ReID, database, VLM, homography ra mét, animation. Không cắt evidence hoặc thay webcam bằng fixture. Mọi thay đổi sau khi khóa config cần run mới và đánh giá lại phần ảnh hưởng.
