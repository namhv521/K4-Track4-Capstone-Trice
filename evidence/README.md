# Quy trình bằng chứng

`synthetic/` chỉ kiểm thử scorer, không phải độ chính xác webcam/model. CLI minh họa:

```powershell
python evaluate.py --events evidence/synthetic/events.csv --labels evidence/synthetic/labels.csv --output evidence/synthetic/metrics.json
```

Kết quả mong đợi synthetic: TP=1, FP=1, FN=1, precision=recall=0.5. Không đưa các số này vào slide như kết quả thật.

## Thu thật

1. Thành viên tự đóng vai, đồng ý quay; không dùng dữ liệu bệnh nhân/sinh viên ngoài đội. Không thu tên/khuôn mặt định danh, không tự upload media.
2. Hiệu chỉnh tối thiểu 4 session riêng, khóa config/model hash trước test. Không chọn lại ngưỡng theo kết quả test.
3. Quay T01 ngồi cạnh đồ; T02 rời để đồ; T03 quay lại <5s; T04 mang đồ đi; T05 che người; T06 đồ chưa được gán; T07 người khác đi ngang. Ghi ít nhất 2 session/cảnh nếu thời gian đủ; báo đúng số thực có.
4. Người D gán nhãn từ video và sidecar timestamp, không xem prediction để quyết định ground truth. Một scenario/session; `t_leave_s` là crossing ra; `t_end_s` là kết thúc clip. `is_abandoned=1` nếu đồ còn sau rời ít nhất 5s. Negative có crossing vẫn ghi thời điểm crossing. Session positive quá ngắn (<5s sau crossing) không đủ đánh giá; ghi lại lý do và quay lại.
5. Chạy `python evaluate.py --events runs/<session>/events.csv --labels evidence/labels.csv --frames runs --output evidence/metrics.json` với CSV events đã gộp đúng session. Scorer từ chối events không có nhãn. Chỉ đưa session test vào CSV gộp; không trộn calibration.
6. Lưu toàn bộ test, kể cả khó/thất bại. Ghi failure ledger với session/video time, nhãn, dự đoán, nguyên nhân có bằng chứng và giới hạn.

## Quy ước metric

- Alert ghép một-một theo session trong [leave+5, min(leave+8,end)]. Early/late là FP và positive không match là FN. Duplicate cùng session/episode/type (hoặc event_id trùng) được đếm riêng, không tăng TP/FP; alert episode khác sau TP là FP.
- TN là số session negative không alert; không phải số frame. Precision/recall mẫu số 0 trả null.
- Reminder chấm riêng [leave, min(leave+3,end)], độ trễ tính từ crossing. Đây là cửa sổ đánh giá, không phải ngưỡng trì hoãn sản phẩm. Schema nhãn hiện tại không có identity truth: association_accuracy=null. Muốn đo chọn đúng người, D cần gán nhãn riêng liên hệ người–đồ từ video; không lấy ID tracker làm ground truth.
- Processing p50/p95 từ processing_ms, không phải trễ người nghe. Alert delay là từ GT crossing tới timestamp event; gồm 5s chủ ý chờ. Dispatch timestamp chỉ chứng minh phát thông báo, chưa chứng minh người nghe.
- UNCERTAIN tích phân trạng thái bên trái giữa 2 frame liên tiếp cách <=0.5s; gap dài báo riêng, không tự tính thành thời gian chắc chắn. Không ngoại suy frame cuối.

## Lỗi thật cần chứng minh

Tìm lỗi candidate: association nhầm khi 2 người gần đồ, ID đổi khi che khuất, hoặc không phát hiện balô. Không sửa log/dự đoán để tạo lỗi. Clip synthetic hoặc lỗi baseline không thay thế lỗi candidate trên camera. Nếu chưa tìm thấy, ghi rõ chưa quan sát được trong số phiên đã thử.
