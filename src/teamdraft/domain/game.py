"""Games and version groups: the user's entry point (REQUIREMENTS R1, R4)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VersionGroup:
    """Games that share learnsets and TMs, e.g. Red + Blue."""

    id: int
    identifier: str
    generation: int


@dataclass(frozen=True)
class Game:
    """One single version the user picks, e.g. Red."""

    id: int
    identifier: str
    name: str
    version_group: VersionGroup

    @property
    def generation(self) -> int:
        return self.version_group.generation
