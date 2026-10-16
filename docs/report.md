# Báo cáo triển khai Trice — cảnh báo đồ không có người trông coi

## Phạm vi và trạng thái bằng chứng

Một webcam cố định, một vùng ghế, người đóng vai tự nguyện, balô/chai nước thuộc các lớp model hỗ trợ. Hệ thống liên hệ track người với đồ trong phiên, không xác thực danh tính hay quyền sở hữu. “Quên đồ” là diễn giải tình huống; camera chỉ quan sát đồ còn lại khi người liên quan rời vùng.

Scorer và bộ test đã triển khai. Ví dụ trong `evidence/synthetic/` chỉ xác minh cách tính, không phải kết quả AI, webcam hoặc độ chính xác triển khai. Chưa có bộ test live được gán nhãn độc lập trong lượt thực hiện này. Không tuyên bố detect chính xác tuyệt đối hoặc nhận đúng chủ đồ.

## Công nghệ và bằng chứng người liên quan

Detector pretrained nhận ảnh BGR và trả box/lớp/confidence. Tracker gán ID tạm giữa các frame; event engine sử dụng hình học, thời gian liên hệ và crossing. Thông tin chính xác về weights, nguồn dữ liệu huấn luyện, version và hash phải lấy từ model card/manifest của A. Không suy diễn confidence detector thành xác suất người đó là chủ đồ.

UI cần hiển thị công nghệ/model đang dùng, ID người/đồ, lý do association và các yếu tố chưa chắc chắn. Người đi ngang không thay chủ; che khuất/mất ID không tự chứng minh đã rời chỗ. Âm thanh/màn hình nhắc tại chỗ không cần nhận diện danh tính. Gửi riêng điện thoại đòi hỏi đăng ký liên kết phiên rõ ràng, ngoài phạm vi camera hiện tại.

## Flow và bảy trụ cột

Ảnh → kiểm tra chất lượng → detection/tracking → biểu diễn người–đồ → kiểm tra association/crossing → state machine → reminder/alert → log/replay → nhãn độc lập và scorer.

| Trụ cột | Thành phần thực thi | Bằng chứng cần lưu |
|---|---|---|
| Học | Detector pretrained | Model card, class, confidence, weights/version/hash; không nhận là tự train |
| Hình học | Box, tâm đồ, đáy giữa người, ROI/crossing | Overlay và config trên camera thật; không suy ra mét từ pixel |
| Bất định | UNCERTAIN khi thiếu bằng chứng | Clip che khuất, log reason, thời gian UNCERTAIN và gap |
| Biểu diễn | Track ID, association, state, episode | Frame và dòng JSONL cùng timestamp |
| Thời gian | Reminder crossing; alert sau 5s | Event timestamp, GT crossing, processing p50/p95 |
| Dữ liệu | Log JSONL, CSV event, replay, nhãn | Consent, manifest, sidecar video, calibration/test riêng |
| Bằng chứng | Scorer và failure ledger | TP/FP/FN, số phiên, ca lỗi thật và giới hạn |

Liên hệ nội dung các lab Phase 2 theo PLAN.md; kỹ thuật không có trong luồng chạy không được ghi là đã tích hợp. Replay offline không chứng minh thời gian thực; box/tracking không phải xác thực danh tính.

## Đánh giá có thể chạy lại

```powershell
python -m unittest discover -s tests -p test_evaluate.py -v
python evaluate.py --events evidence/synthetic/events.csv --labels evidence/synthetic/labels.csv --output evidence/synthetic/metrics.json
```

Nhóm thu thật theo `evidence/README.md`: calibration tách session, T01–T07, nhãn từ video độc lập. Một scenario/session. Đếm alert trong cửa sổ [leave+5, min(leave+8,end)] và reminder riêng trong [leave, min(leave+3,end)]. Không đánh đồng reminder sớm với false alert. Không loại bỏ âm thầm ca khó. Correct association cần nhãn người–đồ riêng; schema hiện có chưa đo được nên scorer trả null.

## Kết quả thực tế

Chưa đo live. Các trường phải điền từ evidence thật:

| Chỉ số | Kết quả |
|---|---|
| Session test / positive / negative | Chưa thu |
| TP / FP / FN / TN session | Chưa đo |
| Precision / recall alert | Chưa đo |
| Delay alert từ crossing p50/p95 | Chưa đo |
| Delay reminder p50/p95 | Chưa đo |
| Processing p50/p95 | Chưa đo |
| Thời gian UNCERTAIN / gap / coverage | Chưa đo |
| Correct association người–đồ | Cần nhãn bổ sung |
| Model/config hash và máy chạy | Lấy từ manifest run |

## Ca lỗi và giới hạn

Chưa có ca lỗi candidate được quan sát live trong lượt này. Thử che người dài, đổi ID khi crossing, hai người gần cùng đồ, đồ bị che. Lưu video time, GT, output, lý do nghi ngờ và điều chưa kết luận được. Không dựng event sai để thay lỗi thật. Nếu thử chưa thấy lỗi thì báo số phiên đã thử và “chưa quan sát”, không kết luận không thể lỗi.

Giới hạn: detector có thể không thấy đồ ngoài lớp hỗ trợ; góc nhìn 2D và che khuất làm association mơ hồ; ID không phải danh tính; camera không biết ý định bỏ quên; cảnh báo phát không chứng minh người đã nghe. Kết quả vài phiên tự diễn không đại diện thư viện hoặc xe bus thật.

## An toàn dữ liệu

Chỉ thành viên tự đóng vai có đồng ý. Không thu dữ liệu thực của bệnh nhân/sinh viên ngoài đội, không xác thực khuôn mặt, không tự upload media. Raw media để local; thống nhất thời hạn xóa và người truy cập trước khi thu. Slide chỉ dùng ảnh được đồng ý và số đo có nguồn run.
