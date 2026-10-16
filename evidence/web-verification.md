# Web localhost verification — 16/10/2026

- 39 tests pass, covering engine/detector/scorer, SQLite persistence/dedup/concurrent writes and web API/WebSocket validation.
- Browser UI verified: video catalog, start video1, displayed actual processed frame with person box/ID, stop, history from SQLite, selected completed session with empty event history.
- video1.avi processed to end via real WebSocket/YOLO pipeline: 365 sampled frames, 369 person/item track measurements summed over frames (not unique people), DB frame_count=365. All states UNASSIGNED; no associated object/event was established at current thresholds/geometry.
- video8.avi and video9.avi: first30 sampled frames each processed; these partial runs do not prove full-video behavior. Both samples had no selected-class detections.
- No independent object/event labels supplied, so no real precision/recall or correct-owner accuracy claimed. Current result shows detection/association limitations on supplied videos, not successful abandonment recognition.
- Video1 73.04 seconds of media took155.52seconds walltime in this test, including model startup/streaming and concurrent UI load. Not real-time throughput proof.
- SQLite stores metadata/events, not raw imagery; supplied video provenance/consent not asserted.

Detailed counts: web-video-test.json and data-video-samples.json. Server remains loopback localhost, no deployment.
