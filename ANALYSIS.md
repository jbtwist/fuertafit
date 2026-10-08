# Analysis: `max_occupancy`

> Analysis produced with **Claude Code, model Opus 5.5, medium effort**.

```python
def max_occupancy(
    bookings: list[tuple[int, int]]
) -> tuple[int, int | None, int | None]:
    """Returns (max_occupancy, peak_start, peak_end)."""
```

Language: **Python**.

---

## 1. Chosen solution and complexity

**Sweep line over two independently sorted arrays (starts and ends) with two pointers.**

1. Validate the input in a single pass and build two flat lists of integers: `starts` and `ends`.
   Invalid entries are logged and skipped (see [section 3](#3-decisions-and-assumptions)).
2. Sort both lists (`sorted()`, which returns new lists; the caller's input is never mutated).
3. Walk both lists with two pointers `i` (starts) and `j` (ends):
   - If `starts[i] < ends[j]` (strict comparison), a booking begins: `current += 1`, `i += 1`.
   - Otherwise a booking ends: `current -= 1`, `j += 1`.
   - The strict `<` processes an end before a start at the same instant, which implements
     half-open intervals `[start, end)`.
4. When `current` becomes **strictly greater** than the best seen so far, record
   `peak_start = starts[i]` and `peak_end = ends[j]` (the earliest pending end).
   Strict `>` keeps the **earliest** peak on ties.
5. The loop can stop once every start has been consumed: occupancy can only go down after that.

Why `ends[j]` is the correct `peak_end`: right after the final peak no new booking can start before
an active one ends, or occupancy would exceed the maximum. So the earliest pending end must belong
to a booking that is active at the peak.

| Resource | Complexity | Notes |
|---|---|---|
| Time | **O(n log n)** | Dominated by the two sorts. Validation and the sweep are O(n). |
| Space | **O(n)** | Two auxiliary lists of `n` integers each. No 2n event tuples are created. |

Lower bound: in the comparison model the problem cannot be solved in less than Ω(n log n), because
it contains element distinctness. Linear time is only possible with extra knowledge of the data
(bounded integer domain, or input already sorted). See [alternative 4](#alternative-4-difference-array--counting-over-a-bounded-domain).

### Behaviour derived from the provided examples

| Example | Rule it establishes |
|---|---|
| `[(9,12),(10,13),(11,14)] -> (3, 11, 12)` | The peak starts at the latest start and ends at the earliest end of the overlapping bookings. |
| `[(9,10),(10,11),(11,12)] -> (1, 9, 10)` | Intervals are half-open (touching bookings do not overlap). On ties, the earliest peak wins. `peak_end` is the first change of the active set, **not** the longest continuous window at max occupancy (that would be `12`). |
| `[] -> (0, None, None)` | Contract for empty input. |

---

## 2. When the solution performs worst

- **Large, unsorted input.** Sorting is the dominant cost. Python's Timsort runs in O(n) on input
  that is already sorted or nearly sorted, and reaches its full O(n log n) cost on random data.
  Bookings that come pre-sorted from the database by start time make the start sort almost free.
- **Very large `n` inside a request.** CPython integers are objects (~28 bytes each, plus 8 bytes
  per list slot). The input plus two auxiliary lists means roughly 3 × n integer references.
  At around 10⁷ bookings, memory reaches hundreds of MB and latency reaches seconds, which is
  unacceptable in a request.
- **Bounded integer domain.** If the values turn out to be small and bounded (for example hours
  0–24), this solution does unnecessary work: alternative 4 is linear.
- **Many invalid entries.** Each invalid entry produces a log line. Logging is I/O, and a heavily
  corrupted dataset can make logging the real bottleneck and flood the logs. The algorithmic
  complexity is unaffected. If this shows up in production, consider aggregating (count plus a
  sample of offending entries) or rate-limiting.
- **Recurrent calls over the same dataset.** Every call re-sorts from scratch. If the same data is
  queried repeatedly, caching the result or maintaining sorted data upstream is cheaper than any
  algorithmic tweak.

---

## 3. Decisions and assumptions

### Interval semantics
- Bookings are **half-open intervals `[start, end)`**. A booking ending at `t` and another starting
  at `t` do not overlap. This is required by example 2.
- On ties, the **earliest peak in time** is returned. This is not the first in input order: input
  order is irrelevant because the data is sorted.
- Input is **not** assumed to be sorted, even though all examples are.
- **Duplicate bookings count separately**: two identical bookings mean occupancy 2.

### `peak_end` — PENDING CONFIRMATION
> **Note:** `peak_end` is currently the **earliest end among the bookings active at `peak_start`**,
> that is, the end of the first elementary segment where the maximum is reached. Example 2 forces
> this reading: occupancy is 1 continuously from 9 to 12, yet the expected `peak_end` is `10`.
>
> A business reading of "when the peak ends" could instead be the **longest continuous window** at
> max occupancy. For `[(0,10),(0,5),(5,10)]` the current rule returns `(2, 0, 5)`, while the window
> reading would return `(2, 0, 10)`.
>
> **This has been raised with the interviewer and is awaiting an answer.** The window variant keeps
> the same O(n log n) / O(n) complexity: it needs events at equal times to be grouped and the sweep
> to continue while occupancy stays at the maximum.

### Integer domain — PENDING CONFIRMATION
- For now, **any integer value is accepted**, including negatives and arbitrarily large values. The
  sweep only compares values, so the sign and magnitude are irrelevant to correctness. Python
  integers do not overflow.
- This has also been raised with the interviewer, because a bounded domain would change the best
  algorithm (see alternative 4). The decision will be revisited when the answer arrives.

### Invalid data: log and continue
An entry is **logged and skipped**, and processing continues. The log includes the offending value
and its index in the input so it can be located in the dataset. An entry is invalid when:

- It is not a 2-element tuple/sequence, or it is `None`.
- Either value is not an `int`, for example a `float`, a `str` or `None`. `bool` is rejected
  explicitly, because in Python it is a subclass of `int`.
- `start == end` (zero duration). Besides being meaningless, it would **break the sweep**: its end
  would be processed before its own start. For example, `[(0,10),(5,5)]` would wrongly yield
  `peak_end = 5` instead of `10`.
- `start > end` (inverted). It could be data corruption or a booking that crosses midnight. With no
  information on the domain it is treated as invalid.

If every entry is invalid, the result is the same as for empty input: `(0, None, None)`.

### Implementation details
- The input list is never mutated (`sorted()` instead of `.sort()`), so the function has no side
  effects on the caller's data.
- Two lists of integers are preferred over 2n `(time, delta)` tuples, to reduce object allocation,
  which is the real cost in CPython.

---

## 4. Rejected alternatives

#### Alternative 0: brute force (compare every booking with every other)
O(n²) time, O(1) space. Rejected: it does not scale to production volumes, as the statement warns
explicitly.

#### Alternative 1: sweep line with `(time, ±1)` events
O(n log n) time, O(n) space. **Considered equivalent to the chosen solution.** It is the same
algorithm with a different data layout: one sorted list of 2n tuples instead of two sorted lists of
integers. The two-array version was chosen because it allocates fewer objects.

#### Alternative 3: sort by start plus a min-heap of active ends
O(n log n) time, O(n) space. Rejected: same asymptotic cost as the chosen solution, but with a
larger constant factor (heap push/pop on every booking) and no practical advantage.

#### Alternative 4: difference array / counting over a bounded domain
O(n + R) time, O(R) space, where R is the size of the value range. Rejected **for now**, because the
integer domain is unknown. With unbounded values (for example epoch timestamps), R can be huge and
the array would be unusable.

**If values are confirmed to be bounded, this becomes the most efficient option**: linear time and
no sorting at all.

#### Alternative 5: vectorized with numpy (`lexsort` + `cumsum` + `argmax`)
O(n log n) time, O(n) space. Not considered interesting for this exercise. It adds an external
dependency and only pays off at very large volumes.

### Benchmarking recommendation
If this function turns out to be **critical and recurrent**, and more information about the incoming
data becomes available (value range, typical and maximum `n`, whether data arrives pre-sorted),
**benchmarks** should be run. They should measure the time needed to process representative
datasets with the chosen solution and with alternative 4. That gives a technical, measured reason
to adopt alternative 4 or not, instead of relying only on asymptotic analysis. Constant factors,
memory allocation of the range array and CPython overhead can change the winner for realistic
sizes of `n` and `R`.
