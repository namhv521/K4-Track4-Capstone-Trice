# A — Computer Vision / Perception

Đọc README, CONTRACTS, MERGE. Chỉ sửa detector.py, requirements-cv.txt, docs/model_card.md, tests/test_detector.py. Đầu vào frame/timestamp từ C; đầu ra observation cho B/C/D.

## 0–30 phút: tháo blocker sớm

- [ ] Tạo .venv trong Trice, kiểm tra camera bằng máy demo; không sửa môi trường lab cũ.
- [ ] Dùng weights nano COCO đã chạy được; kiểm tra person/backpack trên balô thật, đọc model.names.
- [ ] Implement Detector.infer/reset đúng contract; không đổi field hoặc box sang ảnh resize.
- [ ] ByteTrack có sẵn, không tự xây tracker/ReID. Chỉ measurement observed=true.
- [ ] Gửi C/D observation sample và clip smoke trước phút 30, lưu trong runs hoặc data/local.

## 30–80 phút

- [ ] Ghép với C trước phút 45; kiểm tra ID/session reset, class mapping, confidence và JSON serialization.
- [ ] Ghi quality lý do rõ; phát hiện camera gap thuộc C/B. Ảnh giống nhau chưa đủ chứng minh camera đóng băng.
- [ ] Đo inference steady-state, bỏ warmup; log model/imgsz/device/n; không báo inference là end-to-end latency.
- [ ] Pin dependency thật sau chạy thành công; hoàn thiện model card/source/train data/hash/license.

## 80–180 phút

Vận hành camera cho test calibration/test riêng. Không tune test để làm đẹp số. Hỗ trợ tìm candidate failure do balô/ID/che khuất; viết phần model/data cho D và rà deck.

## Kiểm tra và bàn giao

Tạo tests/test_detector.py: coordinate bounds, JSON-serializable, observed measurement, reset stream. Test model/webcam cần thiết bị ghi rõ điều kiện; không dùng synthetic thay kết quả inference thật.

```powershell
python tools/check_contract.py
python -m unittest discover -s tests -p test_detector.py -v
```

Guide chưa tạo test_detector.py; A phải viết. Bàn giao commit/files, environment pin, weights path/hash, lệnh live đã thử, FPS/latency thực và hạn chế. Thiếu model/camera báo ngay ở phút 30; không fake detection.
