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
   This early stop only applies to the current `peak_end` rule (see the pending note in section 3).

Why `ends[j]` is the correct `peak_end`: right after the final peak no new booking can start before
an active one ends, or occupancy would exceed the maximum. So the earliest pending end must belong
to a booking that is active at the peak.

| Resource | Complexity | Notes |
|---|---|---|
| Time | **O(n log n)** | Dominated by the two sorts. Validation and the sweep are O(n). |
| Space | **O(n)** | Two auxiliary lists of `n` integers each. |

Lower bound: in the comparison model the problem cannot be solved in less than Ω(n log n), because
it contains element distinctness. Linear time is only possible with extra knowledge of the data,
such as a bounded integer domain (see [alternative 4](#alternative-4-difference-array-over-a-bounded-domain))
or input that is already sorted.

### Behaviour derived from the provided examples

| Example | Rule it establishes |
|---|---|
| `[(9,12),(10,13),(11,14)] -> (3, 11, 12)` | The peak starts at the latest start and ends at the earliest end of the overlapping bookings. |
| `[(9,10),(10,11),(11,12)] -> (1, 9, 10)` | Intervals are half-open (touching bookings do not overlap). On ties, the earliest peak wins. `peak_end` is the first change of the active set, **not** the longest continuous window at max occupancy (that would be `12`). |
| `[] -> (0, None, None)` | Contract for empty input. |

---

## 2. When the solution performs worst

- **Large, unsorted input.** Sorting is the dominant cost. Python's Timsort is linear on input that
  is already sorted or nearly sorted, and reaches its full O(n log n) cost on random data.
  Bookings that come pre-sorted from the database by start time make the start sort almost free.
- **Very large `n` inside a request.** Memory grows linearly: the input plus two auxiliary lists of
  the same length. Because the function runs inside a request, both latency and memory per request
  grow with the dataset, and there is no upper bound on `n` in the statement.
- **Bounded integer domain.** If the values turn out to be small and bounded, this solution does
  unnecessary work: alternative 4 is linear.
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
> A product reading of "when the peak ends" could instead be the **longest window**, which changes
> two rules at once:
>
> 1. **The peak is a window, not an occurrence.** The peak is the whole continuous period during
>    which occupancy stays at the maximum, even if the set of active bookings changes inside it. For
>    `[(0,10),(0,5),(5,10)]` the current rule returns `(2, 0, 5)`, while the window reading returns
>    `(2, 0, 10)`.
> 2. **On ties, the longest window wins**, not the earliest. For `[(0,2),(1,3),(10,15),(11,14)]` there
>    are two windows at occupancy 2: `[1,2)` and `[11,14)`. The current rule returns `(2, 1, 2)`,
>    while the window reading returns `(2, 11, 14)`. If several windows have the same length, the
>    earliest one would be returned (assumption, to be confirmed as well).
>
> Note that the window reading **contradicts example 2**: occupancy is 1 continuously over `[9,12)`,
> so it would return `(1, 9, 12)` instead of the expected `(1, 9, 10)`.
>
> **This has been raised with the interviewer and is awaiting an answer.** The window variant keeps
> the same O(n log n) / O(n) complexity, with three changes to the sweep:
>
> - Events at the same instant are applied together before reading the occupancy, so an end and a
>   start that cancel out do not split a window.
> - Every window at the current maximum is measured, and the longest one is kept. When a higher
>   maximum appears, the kept window is discarded.
> - The sweep cannot stop once every start has been consumed: it has to process the remaining ends to
>   close the last window.

### Integer domain — PENDING CONFIRMATION
- **Negative values are not accepted**: a booking cannot start or end at a negative time. They are
  treated as invalid data (see below).
- For now, **there is no upper bound**: any non-negative integer is accepted, however large. The
  sweep only compares values, so magnitude is irrelevant to correctness, and Python integers do not
  overflow.
- Whether the domain has an upper bound has been raised with the interviewer, because a bounded
  domain would change the best algorithm (see alternative 4). The decision will be revisited when
  the answer arrives.

### Invalid data: log and continue
An entry is **logged and skipped**, and processing continues. The log includes the offending value
and its index in the input so it can be located in the dataset. An entry is invalid when:

- It is not a 2-element tuple/sequence, or it is `None`.
- Either value is not an `int`, for example a `float`, a `str` or `None`. `bool` is rejected
  explicitly, because in Python it is a subclass of `int`.
- Either value is negative. A booking cannot happen at a negative time.
- `start == end` (zero duration). Besides being meaningless, it would **break the sweep**: its end
  would be processed before its own start. For example, `[(0,10),(5,5)]` would wrongly yield
  `peak_end = 5` instead of `10`.
- `start > end` (inverted). It could be data corruption or a booking that crosses midnight. With no
  information on the domain it is treated as invalid.

### Edge cases
Expected result for each edge case under the current decisions:

| Case | Input | Expected result | Rationale |
|---|---|---|---|
| Empty input | `[]` | `(0, None, None)` | Contract from example 3. |
| Several separate peaks of equal size | `[(0,2),(1,3),(10,12),(11,13)]` | `(2, 1, 2)` | The earliest peak wins. Same result with the window reading: both windows are equally long. |
| Negative values | `[(9,12),(-3,2)]` | `(1, 9, 12)` + log | `(-3,2)` is invalid and skipped. |
| Zero-duration booking | `[(0,10),(5,5)]` | `(1, 0, 10)` + log | `(5,5)` is invalid and skipped. |
| Inverted booking | `[(9,12),(14,9)]` | `(1, 9, 12)` + log | `(14,9)` is invalid and skipped. |
| Malformed entries | `[(9,12), None, (1,2,3), (9.5,12), (True,5)]` | `(1, 9, 12)` + 4 logs | Each invalid entry is logged with its index and skipped. |
| Every entry invalid | `[(5,5),(14,9)]` | `(0, None, None)` + logs | Same as empty input. |

### Implementation details
- **Standard library only.** No external dependencies are used.
- The input list is never mutated (`sorted()` instead of `.sort()`), so the function has no side
  effects on the caller's data.
- Two lists of integers are preferred over a single list of `(time, delta)` tuples, to reduce object
  allocation in CPython.

---

## 4. Rejected alternatives

#### Alternative 1: brute force (compare every booking with every other)
O(n²) time, O(1) space. Rejected: it does not scale to production volumes, as the statement warns
explicitly.

#### Alternative 2: sweep line with `(time, ±1)` events
O(n log n) time, O(n) space. **Considered equivalent to the chosen solution.** It is the same
algorithm with a different data layout: one sorted list of `(time, delta)` tuples instead of two
sorted lists of integers. The two-array version was chosen because it allocates fewer objects.

#### Alternative 3: sort by start plus a min-heap of active ends
O(n log n) time, O(n) space. Rejected: same asymptotic cost as the chosen solution, but with a
larger constant factor (a heap push/pop on every booking) and no practical advantage.

#### Alternative 4: difference array over a bounded domain
O(n + R) time, O(R) space, where R is the size of the value range. Rejected **for now**, because the
integer domain is unknown. With unbounded values (for example epoch timestamps), R can be arbitrarily
large and the array becomes unusable.

**If values are confirmed to be bounded, this becomes the most efficient option**: linear time and
no sorting at all.

The number of arrays it needs depends on the `peak_end` semantics:

- **Earliest occurrence (current rule): two arrays are needed.** A single difference array stores
  the *net* change at each instant, so a booking that ends at `t` and another that starts at `t`
  cancel out. In example 2, the net change at `10` is `0`, and nothing tells the algorithm that a
  booking ended there, so it cannot return `peak_end = 10`. A second array counting the ends at
  each instant fixes this: `peak_end` is the first instant after `peak_start` with at least one end.
- **Longest window (product reading): one array is enough.** The prefix sum of the difference array
  gives the occupancy at each instant. Each window is a run of consecutive instants at the maximum
  occupancy; the longest run is returned (the earliest one if several have the same length). Changes
  that cancel out at the same instant are irrelevant there, and ignoring them is exactly what that
  reading requires.

In both cases the complexity stays O(n + R) time and O(R) space.

### Benchmarking recommendation
If this function turns out to be **critical and recurrent**, and more information about the incoming
data becomes available (value range, typical and maximum `n`, whether data arrives pre-sorted),
**benchmarks** should be run. They should measure the time needed to process representative
datasets with the chosen solution and with alternative 4. That gives a technical, measured reason
to adopt alternative 4 or not, instead of relying only on asymptotic analysis. Constant factors and
the cost of allocating the range array can change the winner for realistic sizes of `n` and `R`.
