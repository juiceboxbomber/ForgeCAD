"""Pure helpers for ForgeCAD's direct selection-driven cope command."""


def _layout_id(obj):
    return str(getattr(obj, "SourceLayoutID", "") or "").strip()


def _xyz(point):
    return (float(point.x), float(point.y), float(point.z))


def _point_key(point, precision=6):
    return tuple(round(value, precision) for value in _xyz(point))


def _end_keys(obj, precision=6):
    if not hasattr(obj, "StartPoint") or not hasattr(obj, "EndPoint"):
        raise ValueError("Select only straight generated ForgeCAD members.")
    return {
        _point_key(obj.StartPoint, precision),
        _point_key(obj.EndPoint, precision),
    }


def selected_cope_request(
    objects,
    precision=6,
):
    """Resolve one straight cope source plus straight-or-bent endpoint targets."""

    objects = list(
        objects
        or ()
    )

    if not (
        2
        <= len(
            objects
        )
        <= 4
    ):
        raise ValueError(
            "Select the straight tube to cope first, then one to three target tubes."
        )

    source = objects[
        0
    ]

    source_id = str(
        getattr(
            source,
            "SourceLayoutID",
            "",
        )
        or ""
    ).strip()

    if not source_id:
        raise ValueError(
            "The tube being coped must currently be a straight generated "
            "ForgeCAD member. Bent tubes are supported as cope targets first."
        )

    from forgecad.services.fabrication_identity import (
        shared_structural_endpoint,
    )

    node_xyz, member_ids = (
        shared_structural_endpoint(
            objects,
            precision=precision,
        )
    )

    if (
        not member_ids
        or member_ids[
            0
        ]
        != source_id
    ):
        raise ValueError(
            "Could not resolve the selected cope source at the shared endpoint."
        )

    target_ids = tuple(
        member_ids[
            1:
        ]
    )

    if not target_ids:
        raise ValueError(
            "Select at least one cope target."
        )

    return (
        node_xyz,
        source_id,
        target_ids,
    )





def replace_source_pairs(existing_pairs, source_id, target_ids):
    source_id=str(source_id or "").strip()
    targets=tuple(str(v or "").strip() for v in target_ids)
    if not source_id or not 1 <= len(targets) <= 3:
        raise ValueError("A cope requires one source and one to three targets.")
    if any(not t or t==source_id for t in targets):
        raise ValueError("Cope targets must be different from the coped tube.")
    if len(set(targets)) != len(targets):
        raise ValueError("Cope targets must be different from each other.")
    kept=[]
    for pair in existing_pairs or ():
        if not isinstance(pair,(list,tuple)) or len(pair)!=2:
            raise ValueError("A stored cope pair is malformed.")
        s=str(pair[0] or "").strip(); t=str(pair[1] or "").strip()
        if not s or not t or s==t:
            raise ValueError("A stored cope pair is malformed.")
        if s != source_id and (s,t) not in kept:
            kept.append((s,t))
    kept.extend((source_id,t) for t in targets)
    return tuple(kept)


