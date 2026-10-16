# Verification status

Implemented modules: real YOLO11n/ByteTrack inference, measured-track temporal association, separate reminder/alert, dashboard with related-person evidence, opt-in local recording/replay, independent-label event evaluator.

Webcam 0 successfully opened at 640x480; integrated live run processed 15 frames and terminated in UNCERTAIN. This proves pipeline execution, not abandoned-object accuracy. No raw webcam imagery saved during this check.

Synthetic engine replay emitted REMINDER at 3.0s and UNATTENDED_ALERT at 8.0s with person #1 / item #7. Synthetic evidence must not be claimed as real-world accuracy.

Pending human verification: staged person/backpack placement and exit, calibrated camera geometry, independent labels, precision/recall on real sessions, and a recorded real candidate failure. One camera cannot prove ownership/intent, hidden people or new identities after ID switches.

Live integrated verification update: processed 50 webcam frames without saving raw media. After excluding 10 initial frames, 40 inference measurements gave p50 about 206 ms and p95 about 278 ms. Reasons included IMAGE_QUALITY and FRAME_GAP; this is pipeline/timing smoke only, not a successful person/backpack scenario. See live_smoke.json.
