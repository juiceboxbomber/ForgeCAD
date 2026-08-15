"""Tooling-aware bent-tube creation services."""

from dataclasses import dataclass

from forgecad.fabrication import (
    BenderTooling,
    BentTube,
)
from forgecad.services.bender_setup import (
    MachineBendInstructions,
    build_machine_bend_instructions,
)


@dataclass(frozen=True, slots=True)
class ToolingAwareBentTube:
    """A created bent tube with optional validated bender tooling."""

    tube: BentTube
    tooling: BenderTooling | None = None

    def __post_init__(self) -> None:
        if not isinstance(
            self.tube,
            BentTube,
        ):
            raise TypeError(
                "tube must be a BentTube instance."
            )

        if (
            self.tooling is not None
            and not isinstance(
                self.tooling,
                BenderTooling,
            )
        ):
            raise TypeError(
                "tooling must be a BenderTooling instance or None."
            )

        if self.tooling is not None:
            # Validation happens through the same service used
            # to build real machine instructions.
            build_machine_bend_instructions(
                self.tube,
                self.tooling,
            )

    @property
    def has_tooling(self) -> bool:
        """Return whether tooling has been assigned."""

        return self.tooling is not None

    def machine_instructions(
        self,
    ) -> MachineBendInstructions | None:
        """Return calibrated machine instructions when tooling exists."""

        if self.tooling is None:
            return None

        return build_machine_bend_instructions(
            self.tube,
            self.tooling,
        )


def attach_tooling(
    tube: BentTube,
    tooling: BenderTooling | None,
) -> ToolingAwareBentTube:
    """Attach optional tooling to a bent tube with validation."""

    return ToolingAwareBentTube(
        tube=tube,
        tooling=tooling,
    )
