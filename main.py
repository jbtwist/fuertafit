import logging

logger = logging.getLogger(__name__)


# Type hints are not enforced at runtime, so the types are checked by hand. In a codebase that
# validates calls with Pydantic this helper would usually not be needed.
def _is_valid_time(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _split_valid_bookings(
    bookings: list[tuple[int, int]],
) -> tuple[list[int], list[int]]:
    """Validate the bookings and return their starts and ends as two flat lists.

    Invalid entries are logged with their index and value, then skipped.
    """
    starts: list[int] = []
    ends: list[int] = []
    for index, booking in enumerate(bookings):
        if not isinstance(booking, (tuple, list)) or len(booking) != 2:
            logger.warning("Skipping booking %d: not a (start, end) pair", index)
            continue
        start, end = booking
        if not (_is_valid_time(start) and _is_valid_time(end)):
            logger.warning(
                "Skipping booking %d: start and end must be non-negative integers: %r",
                index,
                booking,
            )
            continue
        if start >= end:
            logger.warning(
                "Skipping booking %d: start must be strictly before end: %r", index, booking
            )
            continue
        starts.append(start)
        ends.append(end)
    return starts, ends


def max_occupancy(
    bookings: list[tuple[int, int]],
) -> tuple[int, int | None, int | None]:
    """Sort the starts and the ends separately and walk both lists in time order, adding one
    for each start and subtracting one for each end. The highest count reached is the peak.
    """
    starts, ends = _split_valid_bookings(bookings)
    starts.sort()
    ends.sort()

    best = 0
    peak_start: int | None = None
    peak_end: int | None = None
    current = 0
    i = j = 0

    while i < len(starts):
        if starts[i] < ends[j]:
            current += 1
            if current > best:
                best = current
                peak_start = starts[i]
                peak_end = ends[j]
            i += 1
        else:
            current -= 1
            j += 1

    return best, peak_start, peak_end
