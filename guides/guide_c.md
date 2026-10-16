# C — Trưởng tích hợp / UI / Record / Replay

Đọc README, CONTRACTS, MERGE. Sở hữu main.py, recorder.py, tests/test_replay.py, docs/runbook.md; điều phối shared contract/fixture. Không sửa detector/engine/scorer âm thầm.

## 0–30 phút

- [ ] Chốt baseline/ownership, kênh nhắc tại chỗ, timebase và máy demo. Nếu dùng Git thiết lập một lần theo MERGE.
- [ ] App nhận observation fixture và decision, vẽ overlay đơn; không cần web/server.
- [ ] Implement recorder và manifest/config snapshot; session/run riêng, output trong Trice.

## 30–65 phút

- [ ] Ghép camera→Detector.infer→EventEngine.update→overlay trước phút 45.
- [ ] Timestamp live monotonic; timer theo nguồn không theo FPS giả định. Camera lỗi không giữ frame cũ chạy timer.
- [ ] Overlay có LIVE/REPLAY, seat/ID/state/reason/countdown/FPS/latency; chữ đi kèm màu, UNCERTAIN rõ ràng.
- [ ] REMINDER và ALERT khác kênh/nội dung, không phát lặp mỗi frame; màn hình/âm thanh ở nơi người còn nhận.
- [ ] Record MP4, JSONL, events CSV, manifest và video index→t_s sidecar; đóng handles sạch.
- [ ] Phím record/reset/quit và log lý do reset. Replay log reset engine, giữ t_s gốc.

## 65–180 phút

Khóa config cùng B trước test. Khi A chạy máy, C đóng vai, kiểm tra dữ liệu từng phiên cho D. Tạo README/runbook với lệnh thực đã chạy; xuất ảnh/plot hỗ trợ D, ghép deck/report vào bundle. Theo mốc PLAN merge từng module và chạy checks.

## Kiểm tra và bàn giao

Tests replay hai tốc độ cho cùng event timestamps, session reset, dedup, camera gap, writer close/CSV đúng header. Stub hiện chưa hỗ trợ --source/--replay; C triển khai rồi mới công bố lệnh này trong README.

```powershell
python tools/check_contract.py
python -m unittest discover -s tests -v
```

Kiểm tra thêm live positive/negative trên máy cuối; tests không thay thiết bị thật. Không báo “demo hoàn tất” khi chỉ fixture nối được.
