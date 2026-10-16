"""Owner D. No synthetic metrics are returned by this scaffold."""
EVENT_FIELDS = ["session_id", "event_id", "episode_id", "type", "t_s", "seat_id",
                "person_id", "object_id", "reason"]
LABEL_FIELDS = ["session_id", "scenario_id", "is_abandoned", "t_leave_s",
                "t_return_s", "t_end_s", "notes"]


def evaluate(events_path: str, labels_path: str, frames_dir: str) -> dict:
    raise NotImplementedError("D: score real events against independent ground truth")
