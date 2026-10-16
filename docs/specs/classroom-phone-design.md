# Classroom camera, table reminders and phone scanning — design

Status: proposed extension of the local Trice prototype, 16/10/2026. No classroom camera URL or phone pairing has been verified yet.

## Product decision

Observe table zones and a room doorway with the same fixed camera. Associate a measured item/person track within each table zone. Only an observed outward doorway crossing by the related track authorizes a room-exit reminder. Disappearing behind a table or simply walking away from a chair is insufficient. Camera cannot know whether someone is going home rather than briefly leaving.

Broadcast wording: “Bạn ở bàn số A01, vui lòng kiểm tra đồ. Bạn có thể đã để quên ba lô.” Never name a person or assert verified ownership. A room-exit reminder is distinct from a confirmed unattended event after the configured wait. Cancel pending when the related person returns; lost identity is uncertainty, not a new owner.

## Sources and integration

- Existing local videos remain for regression.
- Overall camera: USB index or operator-configured RTSP/HTTP stream. No guessed URL or real-camera proof before connection succeeds. Credentials never returned by API, logged, or committed.
- Phone camera: dedicated mobile page requests rear camera, transmits bounded JPEG frames with backpressure and source timestamps, shows status. Dashboard observes the session independently. Moving camera invalidates a fixed room map until recalibrated; no cross-camera identity association is claimed.
- Phone on another device needs a reachable LAN endpoint plus trusted HTTPS for getUserMedia. HTTP on a LAN IP is generally insufficient. Provide setup instructions, not automatic certificate trust changes or browser security bypasses. Localhost remains the default listener.

## World representation and geometry

A room profile has table IDs/names/polygons, a doorway region, a finite oriented exit line and camera/source ID. All coordinates normalized. Table labels are user configured, not inferred by model. Polygons must be valid/non-overlapping for automatic assignment. Objects on boundaries or ambiguous tables become UNCERTAIN. Several table states can coexist; one related person/item per table is the initial bound. Do not promise crowded-room person re-identification.

Tracking measurements/predictions remain distinct. Store source IDs and measured timestamps; disallow deriving exit from long gaps, unobserved tracks or a crossing of the extended infinite line outside the doorway. Room-wide announcements require the door gate.

## Audio

Primary choice pending operator answer: browser dashboard connected to external speakers, with explicit enable/test voice control and Vietnamese speech voice selection. Browser speech support/voice availability must be surfaced; dispatch is not proof the person heard it. Dedup announcements by episode/table/type, bounded queue/cooldown, distinguish test voice from detection event. Never play real unsolicited announcements while testing inference silently.

## Persistence and replay

SQLite persists room profiles, table-specific state summaries/events, source type, model/config hash and notification dispatch result. Images remain in RAM by default. Replay input log includes source timestamps, per-table decisions, quality and doorway-crossing evidence. Independent labels include table_id and room_exit_time so correct table and timing can actually be evaluated.

## Track 4 application

Direct: detector provenance/input-output (1–3); degraded-data quality/slice selection (4); tracking prediction/measurement and outlier rejection (5/7/8); 2D coordinate conventions and optional ground-plane calibration only when genuinely used (6); versioned data, session split/quality and labels (9/10); controlled occlusion/gap/scenario sweeps (11); replay/evidence-based gates (12). No unrelated LiDAR/VLM/LoRA added merely for coverage.

Seven pillars: learned detector; table/door geometry; uncertainty; room/table/person/item state; source/receive/decision/announcement times; log/labels/replay; correct-table event metrics, latency and real failure. Detailed mapping must reference actual lab files and distinguish direct implementation from methodological links.

## Validation

Tests: multiple table assignment; room-door crossing vs chair departure; line crossing outside door rejected; item carried out; unrelated passerby; ID switch/occlusion; return cancel; missing camera/gap; announcement dedup/test mode; phone disconnect/stale frame; independent dashboard subscription; persistence; invalid profile/network input.

Actual measurements: correct table precision/recall, source-to-decision/dispatch latency with timebase limits, processed FPS and uncertain coverage. Local video smoke is not accuracy. Real camera/phone/speaker trials require the respective devices and operator actions; document explicitly when unverified.
