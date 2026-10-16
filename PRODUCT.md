# Web product context

Trice is a localhost operational dashboard for testing existing person/item detection and abandonment rules. Main input is videos already in Trice/data; browser camera is optional on localhost. FastAPI reuses Detector/EventEngine, SQLite stores session/event metadata only, static HTML/CSS/JS frontend requires no Node build. Related-person evidence and algorithm explanation must be visible. No deployment or public URL in scope. Media provenance and independent labels are still required before accuracy claims.
