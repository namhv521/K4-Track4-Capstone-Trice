# Trice — Nhắc kiểm tra đồ khi rời chỗ

Workspace duy nhất của đội. **Chỉ tạo/sửa/chạy output trong `Trice`**, không sửa lab Phase 2 bên ngoài. Hiện tại đây là bộ khung làm việc và fixture tổng hợp; **chưa có AI/webcam hoặc metric thực**.

## Bắt đầu

```powershell
Set-Location C:\Su\VinLab\phase2-track4\Trice
python tools/check_contract.py
python main.py --fixture fixtures/attended.jsonl
python -m unittest discover -s tests -v
```

Ba lệnh trên chỉ kiểm tra contract và đường nối trên fixture. Module chưa làm sẽ báo `NOT_IMPLEMENTED`, không được coi là demo hoàn tất.

## Mỗi người đọc gì và sửa gì?

| Thành viên | Guide | File sở hữu |
|---|---|---|
| A — CV | [guide_a.md](guides/guide_a.md) | `detector.py`, `requirements-cv.txt`, `docs/model_card.md`, `tests/test_detector.py` |
| B — Engine | [guide_b.md](guides/guide_b.md) | `event_engine.py`, `config.json`, `tests/test_engine.py` |
| C — Integration | [guide_c.md](guides/guide_c.md) | `main.py`, `recorder.py`, `tests/test_replay.py`, `docs/runbook.md` |
| D — Evidence | [guide_d.md](guides/guide_d.md) | `evaluate.py`, `tests/test_evaluate.py`, `evidence/`, `docs/report.md`, `slides/` |

Đọc [CONTRACTS.md](CONTRACTS.md), [PLAN.md](PLAN.md), [MERGE.md](MERGE.md) trước khi code. `fixtures/`, `tools/check_contract.py`, `tests/test_contract.py` là baseline chung; chỉ C điều phối thay đổi contract, có thông báo cho cả đội.

## Sản phẩm cần hoàn thành

Một webcam cố định, một người liên quan, một balô, một ghế và ranh giới rời vùng. Detector/tracker chỉ cung cấp quan sát; engine lưu liên hệ tạm người–đồ, không xác minh danh tính/quyền sở hữu.

- **REMINDER:** nhắc tại chỗ ngay khi có crossing, đồ vẫn còn và đã có association.
- **UNATTENDED_ALERT:** cảnh báo sau 5 giây từ crossing, gồm 2 giây xác nhận; người chưa quay lại, đồ vẫn có measurement.
- **UNCERTAIN:** mất dấu không crossing, mất đồ, ảnh lỗi hoặc ID mơ hồ; không suy luận mất detection = rời đi/đã lấy đồ.

Kênh màn hình/âm thanh phải ở nơi người còn nhận được. Không gửi điện thoại trong MVP. Media chỉ có thành viên đồng ý tự đóng vai, lưu local; không publish mặc định.

## Hoàn tất khi

Live dương/âm chạy thật; tests logic/replay/scorer qua; có video/log/nhãn độc lập; metric có số mẫu; một lỗi candidate thực có giải thích; report và slide khớp evidence. Fixture/smoke không thay thế kiểm chứng này.

Chưa có Git repository khi chuẩn bị workspace. Xem MERGE.md để thiết lập quy trình một lần, không chạy `git init` riêng ở từng module.
