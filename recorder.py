"""Owner C. Recorder contract, not implemented yet."""
import json


def read_frames(log_path: str):
    with open(log_path, encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


class Recorder:
    def __init__(self, session_dir: str, manifest: dict):
        raise NotImplementedError("C: implement local recorder and manifest")

    def write_frame(self, observation: dict, decision: dict, processing_ms: float) -> None:
        raise NotImplementedError("C: write JSONL and deduplicated event CSV")

    def close(self) -> None:
        raise NotImplementedError("C: close video and log handles")
