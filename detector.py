"""Owner A. Contract scaffold only; real inference is not implemented."""


class Detector:
    def __init__(self, model_path: str, config: dict):
        self.model_path = model_path
        self.config = config

    def infer(self, frame_bgr, frame_id: int, t_s: float) -> dict:
        raise NotImplementedError("A: implement real person/backpack detection and tracking")

    def reset(self) -> None:
        raise NotImplementedError("A: reset tracker between sessions")
