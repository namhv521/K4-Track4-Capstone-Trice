"""Stdlib sanity check of the shared scaffold/fixture; not a quality gate for AI."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from event_engine import EventEngine
from recorder import read_frames


def check():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    engine = EventEngine(config)
    count = 0
    for observation in read_frames(str(ROOT / "fixtures/attended.jsonl")):
        assert observation["width"] > 0 and observation["height"] > 0
        for track in observation["tracks"]:
            x1, y1, x2, y2 = track["bbox_xyxy"]
            assert 0 <= x1 < x2 <= observation["width"]
            assert 0 <= y1 < y2 <= observation["height"]
            assert 0 <= track["confidence"] <= 1
        decision = engine.update(observation)
        assert decision["state"] in {"UNASSIGNED", "ATTENDED", "OWNER_LEFT", "ALERT", "UNCERTAIN", "RESOLVED"}
        assert isinstance(decision["events"], list)
        assert not decision["events"], "short attended fixture must not emit events"
        count += 1
    assert count > 0
    return count


if __name__ == "__main__":
    print(f"PASS: {check()} synthetic observations; contract wiring only, live AI not verified")
