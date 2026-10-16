# Classroom and phone implementation plan

Goal: phone rear-camera page produces realtime frames; PC dashboard monitors per-table evidence and speaks table-specific reminders on observed room-door exit. Only Trice changed. User approved phone web input and dashboard PC external speaker on16/10/2026.

Architecture: static mobile producer + scoped RAM pairing token; FastAPI source metadata/backpressure/latest-frame observer; ClassroomEngine per table with finite doorway gate; global camera-motion guard; existing YOLO/ByteTrack; SQLite metadata/events; browser speech queue.

Tasks running in parallel:
- Engine owner: classroom_engine.py, camera_quality.py, tests; map actual Track4 techniques and uncertainty limits.
- Backend owner: phone_security.py, web_backend.py, token/producer/observer isolation, timestamp handling, tests.
- Frontend owner: phone page, pairing controls, classroom zones/settings, table states, speech queue and status.
- Integration owner: HTTPS preparation/user-owned certificate trust instructions, integration tests, real-source smoke, regression and review.

Contract: POST /api/pair {config} local observer -> id/token/phone_fragment; producer websocket first auth JSON then frame metadata+JPEG; /api/sessions/{id}/latest local observer; table decisions/events include table label and Vietnamese announcement. Phone token never query string or SQLite. Existing local videos remain regression input.

Completion checks: regression tests; token expiry/scope/origin; multiple tables and finite door vs chair departure; camera pan invalidates geometry; frontend producer lifecycle/speech controls; persistence; local video pipeline actual inference. Physical phone/trusted certificate/room view/external speaker audibility require operator/device verification and must not be invented.
