"""Reusable tube-profile libraries for ForgeCAD."""

from dataclasses import dataclass, field

from .tube_profile import TubeProfile


@dataclass(slots=True)
class TubeLibrary:
    """Stores named tube profiles and tracks the active selection."""

    profiles: dict[str, TubeProfile] = field(default_factory=dict)
    active_name: str | None = None

    def add(self, name: str, profile: TubeProfile) -> None:
        """Add a named profile to the library."""

        cleaned_name = name.strip()

        if not cleaned_name:
            raise ValueError("Profile name cannot be empty.")

        if cleaned_name in self.profiles:
            raise ValueError(
                f"A tube profile named '{cleaned_name}' already exists."
            )

        self.profiles[cleaned_name] = profile

        if self.active_name is None:
            self.active_name = cleaned_name

    def get(self, name: str) -> TubeProfile:
        """Return a profile by name."""

        try:
            return self.profiles[name]
        except KeyError as error:
            raise KeyError(
                f"Tube profile '{name}' does not exist."
            ) from error

    def set_active(self, name: str) -> None:
        """Set the profile used by new members."""

        if name not in self.profiles:
            raise KeyError(
                f"Tube profile '{name}' does not exist."
            )

        self.active_name = name

    @property
    def active_profile(self) -> TubeProfile:
        """Return the currently active tube profile."""

        if self.active_name is None:
            raise RuntimeError("The tube library has no active profile.")

        return self.profiles[self.active_name]

    @property
    def names(self) -> tuple[str, ...]:
        """Return profile names in insertion order."""

        return tuple(self.profiles)
    