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
    n_substitutions: int = 0     # count of distinct word/unit TYPES actually
                                  # substituted (not occurrences) — 0 for every
                                  # noiser that doesn't do type-level forced
                                  # selection; codemix v2 is the first to set
                                  # this. Additive field with a default so
                                  # every existing call site (which all pass
                                  # keyword args, never positional) keeps
                                  # working unchanged. codemix round 5 changes
                                  # this to occurrence-level UNITS (spans +
                                  # singles), not distinct types — see
                                  # src/noisers/codemix.py's module docstring.
    target_cmi: float = 0.0      # codemix round 5: the per-post Code-Mixing
                                  # Index sampled from that severity's frozen
                                  # band distribution BEFORE fill (see
                                  # src/noisers/codemix.py's _apply()) — the
                                  # DECLARED target, checked against structure
                                  # by eval/invariants.py's check_codemix_
                                  # substitution_spec. The independently
                                  # measured, actually-realised CMI is a
                                  # separate post-hoc computation (eval/cmi.py),
                                  # never just this field echoed back. 0.0 for
                                  # every non-codemix condition (additive
                                  # default, same precedent as n_substitutions).

    def validate(self) -> None:
        assert self.condition in CONDITIONS, self.condition
        assert self.split in ("train", "test"), self.split
        assert self.severity in SEVERITIES + ("none",), self.severity
        assert self.noisy_text.strip(), "empty noisy_text"

    def to_dict(self) -> dict:
        return asdict(self)
