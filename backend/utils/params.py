from dataclasses import dataclass

from flask import Request


@dataclass
class GenerateParams:
    """Validated generation parameters parsed from a Flask request."""

    text: str
    duration: float = 5.0
    rms: float = 0.01
    num_steps: int = 4
    guidance_scale: float = 3.0
    t_shift: float = 0.5
    speed: float = 1.0
    return_smooth: bool = False

    @classmethod
    def from_request(cls, req: Request) -> "GenerateParams":
        text = req.form.get("text", "").strip()
        return cls(
            text=text,
            duration=float(req.form.get("duration", 5)),
            rms=float(req.form.get("rms", 0.01)),
            num_steps=int(req.form.get("num_steps", 4)),
            guidance_scale=float(req.form.get("guidance_scale", 3.0)),
            t_shift=float(req.form.get("t_shift", 0.5)),
            speed=float(req.form.get("speed", 1.0)),
            return_smooth=req.form.get("return_smooth", "false").lower() == "true",
        )
