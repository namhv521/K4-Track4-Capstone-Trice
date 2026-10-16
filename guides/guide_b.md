# B — Hình học / World state / Event Engine

Đọc README, CONTRACTS, MERGE. Chỉ sửa event_engine.py, config.json, tests/test_engine.py. Làm trên fixture, không chờ webcam A. C/D có thể import stub ngay.

## 10–45 phút

- [ ] Viết tests trước cho association và stationary đủ 2 giây, khoảng cách ảnh chuẩn hóa; vật di chuyển chậm không được nhận đứng yên chỉ vì mỗi bước nhỏ.
- [ ] Implement EventEngine/update/reset, bỏ reason NOT_IMPLEMENTED khi có logic thật.
- [ ] ROI/exit config chỉ minh họa: phối hợp C chọn vùng/đường trên camera, geometry_calibrated=true sau kiểm tra.
- [ ] Track đáy giữa người qua đường có hướng/hysteresis bằng measurement cùng ID; mất dấu không phải crossing.
- [ ] Association chỉ giữ một cặp; người đi ngang không được đổi người liên quan.

## 45–80 phút

- [ ] REMINDER ngay crossing khi đồ còn; UNATTENDED_ALERT đủ 5 giây từ crossing, gồm 2 giây confirm; dedup mỗi type/episode.
- [ ] Người quay lại hủy pending; mất người không crossing/mất đồ/ID mơ hồ thành UNCERTAIN.
- [ ] predicted box không xác nhận đồ tồn tại; mất detection không tự RESOLVED.
- [ ] Test gap >0,5 s không cộng thời gian mù; timestamp lùi raise; reset session sạch.
- [ ] Dùng calibration để chọn ngưỡng, khóa config/hash trước phút 80.

## 80–180 phút

Không tune trên test. Dùng replay cùng log để phân tích lỗi và baseline/candidate với D; gửi state diagram, lý do UNCERTAIN và phần trụ cột cho báo cáo. Không gọi khoảng cách ảnh là mét hoặc ID là danh tính.

## Kiểm tra và bàn giao

```powershell
python -m unittest discover -s tests -p test_engine.py -v
python tools/check_contract.py
```

Guide chưa tạo test_engine.py; B phải viết. Bàn giao config, engine/tests, event timestamps mong đợi trên fixture, limitations. Không sửa main/scorer để khớp cách hiểu riêng; hỏi C khi contract thiếu.
