"""Merge automatic/primary cope specs with direct selection-first cope specs."""


def _spec_key(specification):
    return (id(specification.coped_member), str(specification.coped_end))


def merge_direct_cope_specifications(primary_specifications, direct_specifications):
    """Direct cope operations replace primary/automatic cuts on the same member end.

    Multiple direct cuts on the same member end are retained so compound copes
    (for example a diagonal fitted to two mitered rails) continue to work.
    """
    primary = tuple(primary_specifications or ())
    direct = tuple(direct_specifications or ())
    direct_keys = {_spec_key(specification) for specification in direct}
    return tuple(
        specification
        for specification in primary
        if _spec_key(specification) not in direct_keys
    ) + direct
