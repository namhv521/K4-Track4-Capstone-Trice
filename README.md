# Trice — frontend, backend và database local

**Chạy web:**

```powershell
cd C:\Su\VinLab\phase2-track4\Trice
.venv\Scripts\python.exe -m uvicorn web_backend:app --host 127.0.0.1 --port 8000
```

Mở **http://127.0.0.1:8000**. Chọn video trong `data`, bắt đầu để xem YOLO11n + ByteTrack và engine xử lý thật; camera trình duyệt là nguồn tùy chọn. Chưa deploy.

- `web/`: giao diện tiếng Việt, video/box/ROI, người–đồ liên quan, cấu hình, trạng thái, sự kiện và lịch sử.
- `web_backend.py`: FastAPI/WebSocket tái sử dụng detector/engine.
- `storage.py`: SQLite session/events tại `data/trice.sqlite3`; không lưu raw image.
- `detector.py`, `event_engine.py`: perception và quy tắc người–đồ. Track ID tạm, không xác minh ownership/ý định quên.

[Xem hướng dẫn web](docs/web-guide.md), [model card](docs/model_card.md), [evidence](evidence/README.md). Chưa có ground truth độc lập cho video có sẵn nên không tuyên bố precision/recall thực. Kết quả fixture/synthetic không phải độ chính xác camera.

**Tests:** `.venv\Scripts\python.exe -m unittest discover -s tests -v`.

Bộ OpenCV trước vẫn chạy bằng main.py: [runbook](docs/runbook.md). [PLAN](PLAN.md), [CONTRACTS](CONTRACTS.md), [MERGE](MERGE.md), guides/ là phân công module ban đầu; web là phần mở rộng local mới. Toàn bộ công việc và output trong Trice.

## Phòng học, camera điện thoại và loa

Đã bổ sung ClassroomEngine đa vùng bàn/cửa, camera-motion guard, trang phone.html, QR/token pairing và đọc số bàn trên dashboard. Xem [hướng dẫn điện thoại/phòng học/loa](docs/phone-classroom-guide.md) và [pipeline Track4](docs/track4-pipeline.md). Giữ camera cố định để theo dõi crossing; quét bằng camera đang di chuyển chỉ cho detection, không bảo đảm suy luận rời phòng.

Wi-Fi phone cần server HTTPS cùng process với dashboard: `./start-phone.ps1 -LanIP IP_WIFI`, dashboard https://localhost:8443. Bạn tự thiết lập tin cậy CA local/điều kiện mạng; script không sửa trust/firewall. AndroidUSB port forwarding là phương án local khác trong guide. Chưa kiểm chứng điện thoại/loa vật lý.
