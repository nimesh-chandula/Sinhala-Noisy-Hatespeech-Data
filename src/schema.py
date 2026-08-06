"""
Row schema for every generated dataset row. Keep this stable — the eval harness,
the LoRA sampler, and the benchmark all rely on these fields.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict

CONDITIONS = (
    "clean",
    "transliteration",
    "codemix",
    "misspell",
    "abbreviate",
    "compound",
)
SEVERITIES = ("light", "heavy")   # "clean" uses severity "none"


@dataclass
class Row:
    source_id: str          # SOLD post id — links noised back to its origin
    split: str              # "train" | "test"  (never crosses)
    condition: str          # one of CONDITIONS
    severity: str           # "light" | "heavy" | "none"
    original_text: str      # clean Sinhala source
    noisy_text: str         # generated output
    label: int              # inherited from source (0/1)
    realised_noise_rate: float   # actual fraction of tokens altered
    generator_version: str  # bump on every rule change

    def validate(self) -> None:
        assert self.condition in CONDITIONS, self.condition
        assert self.split in ("train", "test"), self.split
        assert self.severity in SEVERITIES + ("none",), self.severity
        assert self.noisy_text.strip(), "empty noisy_text"

    def to_dict(self) -> dict:
        return asdict(self)
