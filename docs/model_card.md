# Model card — Trice perception

## Actual implementation
- Detector: Ultralytics YOLO11n, pretrained COCO detection weights. Image BGR input; original-image boxes, class, detector confidence output.
- Tracker: native Ultralytics ByteTrack (`bytetrack.yaml`), temporary numeric IDs. No face recognition, person re-identification network, names, or ownership verification.
- Default classes: COCO person (0), backpack (24). Optional `object_classes` list can select handbag, suitcase, bottle if those are tested separately.
- Person-to-object association is the event engine responsibility: spatial proximity, persistence, stationary object, then exit crossing. Track ID alone does not identify who owns an object.
- Only current model output is marked `observed=true`; lost-track predictions are not exported. Null IDs cannot establish a reliable tracked owner.
- Simple dark/overexposed gate uses mean pixel intensity. It does not detect every blur, occlusion, frozen camera, or adversarial condition. Confidence is not calibrated probability of correct ownership.

## Provenance
- Weights: `models/yolo11n.pt`, downloaded from https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt
- SHA256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Documentation: https://docs.ultralytics.com/models/yolo11/ and https://docs.ultralytics.com/datasets/detect/coco/
- COCO contains 80 object classes; pretrained weights do not learn forgotten-object intent, VinUni people, or local ownership labels. No local fine-tuning was performed.
- Ultralytics software/model licensing: AGPL-3.0 or Enterprise; see https://www.ultralytics.com/license before distributing a proprietary product. This is a local educational prototype.

## Environment verified on 2026-10-16
`Trice/.venv` uses system-site-packages to read existing torch/OpenCV/numpy without modifying the global lab environment. Locally added ultralytics 8.3.221, lap 0.5.12, torchvision 0.23.0, ultralytics-thop 2.0.18. Existing torch 2.8.0+cu128, OpenCV 4.10.0, numpy 2.3.5. Device default is CPU; explicitly configure CUDA only after checking compatibility. For a clean environment use `python -m pip install -r requirements-cv.txt`.

## Evidence and limits
- Three unit tests pass: valid bounded JSON boxes/current measurements, absent tracker IDs, invalid image/timestamp/reset behavior.
- Real model smoke: one neutral gray 640x480 uint8 frame; YOLO + ByteTrack executed successfully, no objects detected, reset succeeded. First call including model load was 9841.97 ms. This is not steady-state speed, accuracy evidence, or live webcam proof.
- No real person/backpack accuracy measurement has yet been collected. Teammate-only consented webcam sessions and independent event labels are required before reporting precision/recall.
- Similar objects, occlusion, ID switches, crowds, and a person leaving/returning outside the camera can defeat association. The system estimates association, not legal ownership or intent to forget.
- The UI should show detector + tracker + association reason, the linked person's temporary ID and confidence, and `UNCERTAIN` when evidence is insufficient.
