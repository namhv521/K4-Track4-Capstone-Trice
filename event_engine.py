"""Owner B. Neutral scaffold, never a working abandonment detector."""


class EventEngine:
    def __init__(self, config: dict):
        self.config = config
        self.reset()

    def reset(self) -> None:
        self.last_t_s = None

    def update(self, observation: dict) -> dict:
        t_s = observation["t_s"]
        if self.last_t_s is not None and t_s < self.last_t_s:
            raise ValueError("timestamp moved backwards")
        self.last_t_s = t_s
        return {
            "state": "UNASSIGNED", "reason": "NOT_IMPLEMENTED",
            "seat_id": self.config["seat_id"], "person_id": None,
            "object_id": None, "stationary": False, "associated": False,
            "t_exit_s": None, "leave_confirmed": False,
            "elapsed_since_exit_s": 0.0, "remaining_s": None, "events": [],
        }
