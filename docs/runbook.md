# Trice — AI camera nhắc kiểm tra đồ

Đã triển khai trong Trice: YOLO11n COCO + ByteTrack, engine liên hệ người–đồ, crossing/reminder/alert, dashboard bằng OpenCV, recorder/replay và scorer. Chưa chứng minh độ chính xác phát hiện người quên đồ trên bộ test có nhãn độc lập.

## Chạy thật

```powershell
Set-Location C:\Su\VinLab\phase2-track4\Trice
.venv\Scripts\python.exe main.py --source 0 --calibrate --sound
```

Chọn hình chữ nhật bao vùng ghế và vị trí chân người bằng chuột, ENTER xác nhận. Cạnh phải của vùng là đường đi ra; người phải đi từ trái sang phải và còn được camera quan sát khi qua đường. Camera cố định, balô nhìn rõ. Nếu đi theo hướng khác cần B cấu hình exit_line_norm/inside_side trong config.json.

Người và balô ở gần, balô đứng yên đủ 2 giây mới liên kết. Dashboard hiển thị `Related person #ID`, `Item #ID`, ảnh quan sát gần nhất và phương pháp đang dùng: **YOLO detection + ByteTrack + hình học ảnh + quy tắc thời gian**. Ảnh không dùng nhận diện khuôn mặt; ID chỉ tạm trong phiên. Phương pháp không xác minh quyền sở hữu hay ý định quên đồ.

- Khi người liên quan qua đường ra, đồ vẫn còn: REMINDER tại chỗ.
- Đủ 5 giây từ crossing, người chưa quay lại, đồ vẫn quan sát được: UNATTENDED_ALERT.
- Mất dấu không crossing, mất đồ, ID mơ hồ hoặc gap: UNCERTAIN, không gán người khác tùy tiện.
- Q thoát; R reset (kết thúc log đang ghi); S bật/tắt log; C chọn lại vùng. Không che người trước khi camera thấy crossing.
- Hiện chỉ một người liên quan/một món đồ, camera cố định. ID đổi cần reset. Không có gửi thông báo tới tài khoản/điện thoại.

## Ghi và replay

```powershell
.venv\Scripts\python.exe main.py --source 0 --record --sound
```

Ghi JSONL/events/manifest vào runs/session. Thêm `--record-video` chỉ khi người tham gia đồng ý ghi hình; video raw local và timestamp sidecar không commit. `--record` đơn không lưu raw video. File video có sẵn hỗ trợ `--source data/local/ten_video.avi`; provenance/đồng ý dùng dữ liệu cần đội xác nhận trước đánh giá.

```powershell
.venv\Scripts\python.exe main.py --replay runs/SESSION/frames.jsonl
python main.py --fixture fixtures/engine/confirmed_exit.jsonl --headless
```

Replay JSONL không chứa ảnh raw, nền ghi rõ LOG REPLAY; không giả ảnh người. Fixture luôn ghi SYNTHETIC, chỉ kiểm tra logic.

## Đánh giá và kiểm tra

```powershell
.venv\Scripts\python.exe evaluate.py --events runs/SESSION/events.csv --labels data/local/ground_truth.csv --frames runs/SESSION --output evidence/metrics.json
.venv\Scripts\python.exe -m unittest discover -s tests -v
python tools/check_contract.py
```

Thay SESSION bằng thư mục thật. Nhãn độc lập đúng schema CONTRACTS, không lấy output AI làm ground truth. Alert được chấm riêng reminder. Metric ví dụ evidence/synthetic chỉ kiểm tra scorer, không là độ chính xác webcam.

## Phối hợp

[PLAN](PLAN.md), [CONTRACTS](CONTRACTS.md), [MERGE](MERGE.md), guides/guide_a.md đến guide_d.md phân công file và trụ cột. Đã ghép module A/B/C/D trong working tree hiện tại; chưa commit/push thay đổi. Chỉ làm trong Trice.
