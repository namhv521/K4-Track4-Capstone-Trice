# Trice Web — localhost

## Chạy

```powershell
Set-Location C:\Su\VinLab\phase2-track4\Trice
.venv\Scripts\python.exe -m uvicorn web_backend:app --host 127.0.0.1 --port 8000
```

Mở http://127.0.0.1:8000. Hoặc chạy `./start-web.ps1`. Server chỉ lắng nghe loopback; chưa deploy. Frontend HTML/CSS/JS được FastAPI phục vụ cùng origin, không cần npm build.

Môi trường hiện tại đã có dependencies. Trên máy khác: tạo .venv riêng trong Trice rồi `python -m pip install -r requirements-web.txt`; model cần nằm ở models/yolo11n.pt theo docs/model_card.md.

## Test video có sẵn

Chọn **Video trong data**, chọn video1.avi/video8.avi/video9.avi rồi bắt đầu. Backend tự đọc video từ danh sách an toàn dưới Trice/data, lấy mẫu khoảng 5 FPS, timestamp theo frame gốc. Tốc độ xử lý không phải tốc độ video thật; tiến độ hiển thị theo nguồn. Dừng để giải phóng session/model.

Các video hiện có không kèm nhãn bỏ quên độc lập. Nhận được box hoặc xử lý hết video chưa chứng minh đúng người/chủ đồ. Không gán output model thành nhãn. Nếu đồ không được model nhận diện hoặc geometry chưa phù hợp, không có association/alert là kết quả cần phân tích, không tự tạo cảnh báo cho đẹp demo.

## Cấu hình

Chọn tab cấu hình trước phiên. ROI và đường ra dùng tọa độ chuẩn hóa [0,1]; mặc định hình minh họa, cần điều chỉnh theo video. Quy tắc hiện xét cạnh ra có hướng, một người liên quan/một đồ; ID đổi cần phiên mới. Lưu cấu hình giao diện áp dụng cho session mới, không sửa ngầm config của phiên đang chạy.

## Camera trình duyệt

Chọn camera, cấp quyền trên localhost. Trình duyệt gửi JPEG từng frame tới backend cùng máy, chờ kết quả trước frame tiếp theo để không dồn hàng đợi. Dừng/đổi nguồn giải phóng camera. Chưa cấu hình truy cập từ máy khác trong phiên bản localhost này.

## Database và riêng tư

SQLite tại data/trice.sqlite3, WAL. Lưu session/config, counters/state và sự kiện dedup; không lưu JPEG/crop/raw video vào DB. Crop người–đồ chỉ ở RAM session và trình duyệt. Lịch sử phiên/sự kiện đọc từ DB, tồn tại sau khi khởi động lại. Không phải hệ xác minh danh tính hay quyền sở hữu. Không public media người ngoài.

## API

- GET /api/status, /api/config, /api/videos
- POST /api/sessions với config và video_id tùy chọn
- WebSocket /ws/{id}: video tự phát kết quả; camera gửi JPEG binary
- GET /api/sessions; GET /api/sessions/{id}/events
- POST /api/sessions/{id}/stop

## Kiểm tra

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe tools/test_web_videos.py
```

Lệnh thứ hai cần server đang chạy, chạy hết video đầu rồi test 30 frame xử lý của mỗi video còn lại; tạo evidence/web-video-test.json. Đây là evidence pipeline, không phải metric chính xác sự kiện.

Giao diện OpenCV cũ vẫn còn ở main.py; xem docs/runbook.md. Các guide thành viên giữ vai trò kế hoạch ban đầu, web_backend/storage/web là phần mở rộng đã được yêu cầu sau đó.
