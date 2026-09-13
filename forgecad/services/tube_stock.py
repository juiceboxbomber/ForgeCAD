"""Pure-Python tube stock planning for ForgeCAD."""

from dataclasses import dataclass


DEFAULT_STOCK_LENGTH_MM = 6096.0
DEFAULT_SAW_KERF_MM = 3.175
_LENGTH_TOLERANCE_MM = 1e-9


@dataclass(frozen=True, slots=True)
class StockPiece:
    """One fabricated tube piece assigned to stock."""

    member_id: str
    member_name: str
    tube_profile: str
    material: str
    length_mm: float

    @property
    def display_name(self) -> str:
        """Return the most useful shop-floor piece label."""

        if self.member_name:
            return self.member_name

        if self.member_id:
            return self.member_id

        return "Tube Piece"


@dataclass(frozen=True, slots=True)
class StockStick:
    """One purchased stock stick and the pieces cut from it."""

    stick_number: int
    stock_length_mm: float
    saw_kerf_mm: float
    pieces: tuple[StockPiece, ...]

    @property
    def piece_count(self) -> int:
        """Return the number of pieces assigned to this stick."""

        return len(self.pieces)

    @property
    def piece_length_mm(self) -> float:
        """Return finished-piece length assigned to this stick."""

        return sum(
            piece.length_mm
            for piece in self.pieces
        )

    @property
    def cut_count(self) -> int:
        """Return modeled saw cuts for this stick."""

        return len(self.pieces)

    @property
    def kerf_loss_mm(self) -> float:
        """Return total modeled saw-kerf loss."""

        return (
            self.cut_count
            * self.saw_kerf_mm
        )

    @property
    def used_length_mm(self) -> float:
        """Return stock consumed by finished pieces plus kerf."""

        return (
            self.piece_length_mm
            + self.kerf_loss_mm
        )

    @property
    def drop_length_mm(self) -> float:
        """Return leftover stock length."""

        drop = (
            self.stock_length_mm
            - self.used_length_mm
        )

        if abs(drop) <= _LENGTH_TOLERANCE_MM:
            return 0.0

        return drop


@dataclass(frozen=True, slots=True)
class StockProfilePlan:
    """Stock plan for one tube profile and material."""

    tube_profile: str
    material: str
    stock_length_mm: float
    saw_kerf_mm: float
    sticks: tuple[StockStick, ...]

    @property
    def stick_count(self) -> int:
        """Return purchased stick quantity."""

        return len(self.sticks)

    @property
    def piece_count(self) -> int:
        """Return fabricated piece quantity."""

        return sum(
            stick.piece_count
            for stick in self.sticks
        )

    @property
    def total_piece_length_mm(self) -> float:
        """Return total finished-piece length."""

        return sum(
            stick.piece_length_mm
            for stick in self.sticks
        )

    @property
    def total_kerf_loss_mm(self) -> float:
        """Return total modeled kerf loss."""

        return sum(
            stick.kerf_loss_mm
            for stick in self.sticks
        )

    @property
    def total_stock_length_mm(self) -> float:
        """Return total purchased stock length."""

        return (
            self.stick_count
            * self.stock_length_mm
        )

    @property
    def total_drop_length_mm(self) -> float:
        """Return total leftover stock length."""

        return sum(
            stick.drop_length_mm
            for stick in self.sticks
        )


@dataclass(frozen=True, slots=True)
class TubeStockPlan:
    """Complete stock plan grouped by tube profile and material."""

    profile_plans: tuple[StockProfilePlan, ...]
    stock_length_mm: float
    saw_kerf_mm: float

    @property
    def profile_count(self) -> int:
        """Return number of distinct profile/material stock groups."""

        return len(self.profile_plans)

    @property
    def stick_count(self) -> int:
        """Return total purchased stick quantity."""

        return sum(
            plan.stick_count
            for plan in self.profile_plans
        )

    @property
    def piece_count(self) -> int:
        """Return total fabricated piece quantity."""

        return sum(
            plan.piece_count
            for plan in self.profile_plans
        )

    @property
    def total_piece_length_mm(self) -> float:
        """Return total finished-piece length."""

        return sum(
            plan.total_piece_length_mm
            for plan in self.profile_plans
        )

    @property
    def total_kerf_loss_mm(self) -> float:
        """Return total modeled saw-kerf loss."""

        return sum(
            plan.total_kerf_loss_mm
            for plan in self.profile_plans
        )

    @property
    def total_stock_length_mm(self) -> float:
        """Return total purchased stock length."""

        return sum(
            plan.total_stock_length_mm
            for plan in self.profile_plans
        )

    @property
    def total_drop_length_mm(self) -> float:
        """Return total leftover stock length."""

        return sum(
            plan.total_drop_length_mm
            for plan in self.profile_plans
        )


def _numeric_length(value, name: str) -> float:
    """Return a validated finite positive numeric length."""

    try:
        result = float(
            getattr(
                value,
                "Value",
                value,
            )
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{name} must be numeric."
        ) from error

    if result <= 0.0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    if result != result or result in (
        float("inf"),
        float("-inf"),
    ):
        raise ValueError(
            f"{name} must be finite."
        )

    return result


def _numeric_nonnegative(value, name: str) -> float:
    """Return a validated finite nonnegative numeric value."""

    try:
        result = float(
            getattr(
                value,
                "Value",
                value,
            )
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{name} must be numeric."
        ) from error

    if result < 0.0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    if result != result or result in (
        float("inf"),
        float("-inf"),
    ):
        raise ValueError(
            f"{name} must be finite."
        )

    return result


def _piece_from_cut_list_item(item) -> StockPiece:
    """Convert one Cut List item into a stock-planning piece."""

    length_mm = _numeric_length(
        getattr(
            item,
            "length_mm",
            None,
        ),
        "piece length",
    )

    tube_profile = str(
        getattr(
            item,
            "tube_profile",
            "",
        )
    ).strip()

    if not tube_profile:
        raise ValueError(
            "Every stock-planning piece requires a tube profile."
        )

    material = str(
        getattr(
            item,
            "material",
            "",
        )
    ).strip()

    return StockPiece(
        member_id=str(
            getattr(
                item,
                "member_id",
                "",
            )
        ).strip(),
        member_name=str(
            getattr(
                item,
                "member_name",
                "",
            )
        ).strip(),
        tube_profile=tube_profile,
        material=material,
        length_mm=length_mm,
    )


def _piece_consumption_mm(
    piece: StockPiece,
    saw_kerf_mm: float,
) -> float:
    """Return modeled stock consumed by one cut piece."""

    return (
        piece.length_mm
        + saw_kerf_mm
    )


def _plan_profile(
    pieces: list[StockPiece],
    stock_length_mm: float,
    saw_kerf_mm: float,
) -> tuple[StockStick, ...]:
    """Plan one profile using deterministic best-fit decreasing."""

    sorted_pieces = sorted(
        pieces,
        key=lambda piece: (
            -piece.length_mm,
            piece.member_id,
            piece.member_name,
        ),
    )

    open_sticks: list[
        dict[str, object]
    ] = []

    for piece in sorted_pieces:
        consumption = _piece_consumption_mm(
            piece,
            saw_kerf_mm,
        )

        if (
            consumption
            - stock_length_mm
            > _LENGTH_TOLERANCE_MM
        ):
            label = (
                piece.member_name
                or piece.member_id
                or "tube piece"
            )

            raise ValueError(
                f"{label!r} requires "
                f"{consumption:.3f} mm including kerf, "
                f"which exceeds the "
                f"{stock_length_mm:.3f} mm stock length."
            )

        best_index = None
        best_remainder = None

        for index, stick in enumerate(
            open_sticks
        ):
            used_length_mm = float(
                stick[
                    "used_length_mm"
                ]
            )

            new_used = (
                used_length_mm
                + consumption
            )

            if (
                new_used
                - stock_length_mm
                > _LENGTH_TOLERANCE_MM
            ):
                continue

            remainder = (
                stock_length_mm
                - new_used
            )

            if (
                best_remainder is None
                or remainder
                < best_remainder
                - _LENGTH_TOLERANCE_MM
            ):
                best_index = index
                best_remainder = remainder

        if best_index is None:
            open_sticks.append(
                {
                    "pieces": [
                        piece
                    ],
                    "used_length_mm": (
                        consumption
                    ),
                }
            )
        else:
            selected = open_sticks[
                best_index
            ]

            selected_pieces = selected[
                "pieces"
            ]

            selected_pieces.append(
                piece
            )

            selected[
                "used_length_mm"
            ] = (
                float(
                    selected[
                        "used_length_mm"
                    ]
                )
                + consumption
            )

    return tuple(
        StockStick(
            stick_number=index,
            stock_length_mm=(
                stock_length_mm
            ),
            saw_kerf_mm=(
                saw_kerf_mm
            ),
            pieces=tuple(
                stick[
                    "pieces"
                ]
            ),
        )
        for index, stick in enumerate(
            open_sticks,
            start=1,
        )
    )


def plan_tube_stock(
    cut_list,
    stock_length_mm: float = (
        DEFAULT_STOCK_LENGTH_MM
    ),
    saw_kerf_mm: float = (
        DEFAULT_SAW_KERF_MM
    ),
) -> TubeStockPlan:
    """
    Build a deterministic tube stock plan from a Cut List.

    Pieces are grouped by tube profile and material so incompatible
    stock is never mixed. Within each group, a best-fit-decreasing
    one-dimensional packing heuristic is used.
    """

    stock_length_mm = _numeric_length(
        stock_length_mm,
        "stock length",
    )

    saw_kerf_mm = _numeric_nonnegative(
        saw_kerf_mm,
        "saw kerf",
    )

    items = list(
        getattr(
            cut_list,
            "items",
            (),
        )
    )

    grouped: dict[
        tuple[str, str],
        list[StockPiece],
    ] = {}

    order: list[
        tuple[str, str]
    ] = []

    for item in items:
        piece = _piece_from_cut_list_item(
            item
        )

        key = (
            piece.tube_profile,
            piece.material,
        )

        if key not in grouped:
            grouped[
                key
            ] = []
            order.append(
                key
            )

        grouped[
            key
        ].append(
            piece
        )

    profile_plans = []

    for tube_profile, material in order:
        pieces = grouped[
            (
                tube_profile,
                material,
            )
        ]

        profile_plans.append(
            StockProfilePlan(
                tube_profile=(
                    tube_profile
                ),
                material=material,
                stock_length_mm=(
                    stock_length_mm
                ),
                saw_kerf_mm=(
                    saw_kerf_mm
                ),
                sticks=_plan_profile(
                    pieces,
                    stock_length_mm,
                    saw_kerf_mm,
                ),
            )
        )

    return TubeStockPlan(
        profile_plans=tuple(
            profile_plans
        ),
        stock_length_mm=(
            stock_length_mm
        ),
        saw_kerf_mm=(
            saw_kerf_mm
        ),
    )
