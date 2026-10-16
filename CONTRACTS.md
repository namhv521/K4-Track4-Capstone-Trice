# Contract v1 — mọi thành viên dùng chung

Chỉ C điều phối thay đổi. Module dùng dict JSON đơn giản, không cần server/schema framework. Tên file/signature là cố định; implementation bên trong do chủ file quyết định.

## A: detector.py

`Detector(model_path: str, config: dict)`; `infer(frame_bgr, frame_id: int, t_s: float) -> dict`; `reset() -> None`.

Observation:

```json
{"frame_id":0,"t_s":0.0,"width":640,"height":480,"quality_ok":true,"quality_reasons":[],"tracks":[{"id":1,"class_name":"person","bbox_xyxy":[40,30,250,460],"confidence":0.9,"observed":true}],"inference_ms":0.0}
```

Box pixel ảnh gốc, hợp lệ trong width/height. ID int hoặc null; chỉ measurement mới observed=true. Tách predicted track khỏi measurement; không tự cho predicted box xác nhận đồ còn. Dữ liệu phải JSON-serializable.

## B: event_engine.py

`EventEngine(config: dict)`; `update(observation: dict) -> dict`; `reset() -> None`.

Decision gồm: `state`, `reason`, `seat_id`, `person_id`, `object_id`, `stationary`, `associated`, `t_exit_s`, `leave_confirmed`, `elapsed_since_exit_s`, `remaining_s`, `events`.

State: UNASSIGNED/ATTENDED/OWNER_LEFT/ALERT/UNCERTAIN/RESOLVED. Mỗi event gồm `event_id`, `episode_id`, `type`, `t_s`, `seat_id`, `person_id`, `object_id`, `reason`. Type chỉ REMINDER hoặc UNATTENDED_ALERT. `events=[]` khi không có event mới. Dedup `(session_id,episode_id,type)`; một episode có tối đa một event mỗi type.

`t_s` là giây từ đầu session. Engine không đọc clock/camera/disk. Gap >0,5 s làm gián đoạn bằng chứng; timestamp lùi bị từ chối. ROI chuẩn hóa; người dùng đáy giữa box, vật dùng tâm. Geometry trong config chỉ minh họa, C/B phải cấu hình trên camera thật.

Reminder khi crossing hướng ra có association+đồ hiện diện. Alert đủ 5 s từ crossing, 2 s xác nhận nằm trong 5 s. Mất người không crossing/mất đồ/đổi ID mơ hồ thành UNCERTAIN; không tự RESOLVED. Người quay lại hủy pending. Người đi ngang không tự thay association.

## C: recorder.py và main.py

`Recorder(session_dir: str, manifest: dict)`; `write_frame(observation: dict, decision: dict, processing_ms: float) -> None`; `close() -> None`.

`read_frames(log_path: str)` trả iterator các dòng. JSONL record: `{schema_version:1,session_id,observation,decision,processing_ms}`. Event CSV dùng FIELDS của evaluate.py. Chưa gọi recorder stub là chức năng ghi log hoàn tất.

C tạo timestamp monotonic live; replay dùng observation.t_s cũ, không dùng tốc độ đọc file. Reset engine/detector giữa session. Manifest có model/config hash, versions, source, resolution, timebase, consent. Video index ↔ t_s có sidecar khi ghi MP4 fixed FPS. Ghi dispatch time nếu có kênh nhắc; không gọi API dispatch là thời điểm người đã nghe.

## D: evaluate.py

`evaluate(events_path: str, labels_path: str, frames_dir: str) -> dict`.

Ground truth CSV: `session_id,scenario_id,is_abandoned,t_leave_s,t_return_s,t_end_s,notes`. Missing để trống; is_abandoned dùng 0/1. Nhãn độc lập, không chứa dự đoán. Event CSV: `session_id,event_id,episode_id,type,t_s,seat_id,person_id,object_id,reason`.

Chấm UNATTENDED_ALERT riêng, ghép một-một trong [t_leave_GT+5, min(t_leave_GT+8,t_end)]. TP/FP/FN event; TN là phiên âm không alert. Duplicate không tăng TP. Precision=TP/(TP+FP), recall=TP/(TP+FN); mẫu số 0 trả null. Reminder chấm độ trễ/correct association riêng, không tính là alert sớm FP.

## Fixture

`fixtures/attended.jsonl` là chuỗi observation, không phải full recorder record. `fixtures/*.jsonl` chỉ synthetic. `tests/test_contract.py` là sanity test, không chứng minh logic đúng. Chủ B/D phải thêm tests riêng theo guide.
