Technical test by **Juan Villarejo** for **Fuertafit**.

The goal is to find the peak of concurrency in classes from a collection of bookings: given a list
of `(start, end)` bookings, `max_occupancy` returns the maximum number of bookings that overlap at
the same time, together with when that peak starts and ends.

```python
>>> max_occupancy([(9, 12), (10, 13), (11, 14)])
(3, 11, 12)
```

## About this test

Some parts of the statement are open to interpretation. While waiting for the interviewer to answer
those questions, a number of assumptions have been made. They are documented, with their rationale,
in [ANALYSIS.md](ANALYSIS.md).

The test was completed within the established time limit. If the interviewer answers later and
changes are needed, they will be made without hesitation: they simply could not be made earlier.

## Tech stack

- **Vanilla Python**: standard library only, no external dependencies.
- **`unittest`** for the tests, so nothing has to be installed.

## Installation

Requirements: **Python 3.10 or later** (the code uses `int | None` type hints).

```bash
git clone https://github.com/jbtwist/fuertafit.git
cd fuertafit
python3 --version
```

There are no dependencies to install and no virtual environment is required.

## Usage

`max_occupancy` is a plain function. From the repository root, import it and call it with a list of
bookings:

```bash
python3 -c "from max_occupancy import max_occupancy; print(max_occupancy([(9, 12), (10, 13), (11, 14)]))"
```

Output:

```
(3, 11, 12)
```

Or from an interactive session:

```python
>>> from max_occupancy import max_occupancy
>>> max_occupancy([(9, 10), (10, 11), (11, 12)])
(1, 9, 10)
>>> max_occupancy([])
(0, None, None)
```

Invalid bookings (malformed entries, non-integer or negative values, zero-duration or inverted
bookings) are logged as warnings and skipped.

## Running the tests

From the repository root:

```bash
python3 -m unittest discover -s tests
```

Add `-v` to see each test by name:

```bash
python3 -m unittest discover -s tests -v
```

## Authorship

Developed with the support of **Claude Code (Opus 5.5, medium effort)** and reviewed by the author.
