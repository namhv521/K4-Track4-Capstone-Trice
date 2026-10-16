"""Owner C. Fixture wiring only; webcam/UI/recording remain to implement."""
import argparse
import json
from pathlib import Path
from event_engine import EventEngine
from recorder import read_frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    engine = EventEngine(json.loads((root / "config.json").read_text(encoding="utf-8")))
    print("SYNTHETIC FIXTURE ONLY — NOT A LIVE DEMO")
    for observation in read_frames(args.fixture):
        print(json.dumps({"frame_id": observation["frame_id"],
                          "decision": engine.update(observation)}))


if __name__ == "__main__":
    main()
