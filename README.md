# Free-Flood-It on three-colored 3 × n boards

**All code in this repository was generated entirely by AI**, including the original solver, the package interface, command-line tools, and tests. A human directed the research and requested this release. This statement describes code authorship; it does not certify the underlying mathematical claims.

**本仓库的全部代码均由 AI 生成。**

## Supported problem

The input is a complete rectangular grid with exactly three rows and positive width `n`. Cells have colors `0`, `1`, or `2`; using fewer colors is allowed. Adjacency is horizontal or vertical, with no diagonal edges or missing cells.

One Free-Flood-It move chooses any cell and changes its entire current maximal monochromatic connected component to a different palette color. The chosen cell can vary between moves. The goal is to make the whole board monochromatic, with no prescribed final color, using the minimum number of moves.

This implementation is specialized to this model. The internal template generator accepting a height argument does not make the complete solver an implementation for arbitrary heights.

## Quick start

Python 3.10 or later is required. There are no runtime dependencies outside the Python standard library. From the repository root, run:

```sh
python -m floodit3 --rows 0001 2010 0101
```

The command writes JSON. For this example, the relevant fields are:

```json
{
  "status": "solved",
  "free": 3,
  "strokes": 4,
  "moves": [[6, 0], [4, 0], [0, 1]],
  "final_rows": ["1111", "1111", "1111"],
  "replay_verified": true
}
```

Additional fields describe the compiled system, timing, and the recovered certificate. Move choices can change with implementation revisions even when the value stays the same. A move `[v, c]` selects cell `v` and target color `c`. Indices are zero-based in row-major order: `v = row * n + column`.

Save the same JSON to a file with:

```sh
python -m floodit3 --rows 0001 2010 0101 --output results/example.json
```

To install the package and its command-line entry point:

```sh
python -m pip install .
floodit3 --rows 010 010 010
```

Setuptools is used only for building/installing the package. Running directly from a checkout does not require installation.

## Python interface

```python
from floodit3 import replay, solve_board

rows = ("0001", "2010", "0101")
result = solve_board(rows)
assert result["free"] == 3
assert result["replay_verified"]
final_rows = replay(rows, result["moves"])
assert len(set("".join(final_rows))) == 1
```

`solve_board` validates the board, invokes the solver, reconstructs a strategy, and replays that strategy using a separate grid traversal. `replay` can also check external move sequences; it returns the resulting rows and raises `ValueError` for malformed or illegal moves. It does not require the supplied sequence to finish the game.

Run Python without `-O` or `PYTHONOPTIMIZE`: the implementation retains assertions used to check internal certificates, and the public solver refuses optimized mode.

## Bounds and output status

By default, the solver computes a legal greedy strategy and uses its cost as an upper bound. This strategy is only a bound; it is not the returned optimization method.

The optional `--painting-cap T` / `solve_board(..., painting_cap=T)` bounds the internal **number of painting strokes**, which is one more than the flooding move count. It must be between 1 and the number of cells. For example:

```sh
python -m floodit3 --rows 010 010 010 --painting-cap 1
```

This returns `status: "no_solution_within_cap"`, with `free`, `strokes`, and `moves` set to `null`. It is a cap-limited search result, not a claim that the board cannot be flooded. Use the default cap for an unrestricted run. `--no-prune` disables spent-cost pruning for comparison; it does not select a different game model.

## Algorithm and practical limits

The solver represents a strategy as a painting tree, compiles compatible column templates with frontier connectivity information, and stores unbounded common-ancestor chains using a weighted pushdown system. A minimum-weight saturation procedure produces a certificate, from which the code recovers legal Free-Flood-It moves. See [the algorithm notes](docs/algorithm.md) for the roles of the modules and the interpretation of costs.

This is a conservative research implementation. Template generation and transition compilation can become expensive, and the weighted pushdown computation can require substantial memory. It is intended for inspecting the construction and experimenting on small inputs; no claim of practical performance on large boards is made. The source analysis gives a coarse `O(N^13)` bound on compiled-system size, where `N = 3n`; **this is not an `O(N^13)` running-time claim**.

A successful independent replay checks that the returned moves are legal and flood the board. It does not by itself prove that the move count is optimal. General optimality and asymptotic claims require the mathematical arguments behind the construction, beyond the finite regression tests in this repository.

## Tests and validation

Run the tests from a checkout:

```sh
python -m unittest discover -s tests -v
```

To run the same suite and update its machine-readable report:

```sh
python tests/run_validation.py
```

The recorded local run used Python 3.12.14 and passed 12 test methods. Independent breadth-first search checks optimal values on all **122 color-canonical 3 × 2 boards**, 16 deterministic 3 × 3 samples, and the 3 × 4 example above. The latter has Free optimum 3, while the best fixed-root optimum over all 12 possible roots is 4. Other checks cover move replay, malformed inputs, explicit caps, disabled pruning, palette permutations, CLI JSON/file agreement, and zero-cost cycles in the weighted pushdown evaluator. The precise scope is recorded in [validation/test-report.json](validation/test-report.json).

The package includes a GitHub Actions workflow for Linux and Windows with Python 3.10, 3.12, and 3.13. Those jobs run when the repository is hosted on GitHub; their inclusion is not a claim that every CI environment has already been tested locally.

Earlier research records contain broader finite experiments, including exhaustive color-canonical 3 × 3 comparisons. Those experiments are not rerun or bundled as release evidence here. See [the provenance notes](docs/provenance.md) for the source history and the distinction between historical records and this release's checks.

## Repository layout

```text
floodit3/                  Solver, strategy recovery, public API, and CLI
tests/                     Independent small-board BFS and regression tests
examples/boards.json       Small examples with expected move counts
docs/algorithm.md          Construction and implementation notes
docs/provenance.md         Source history and packaging changes
docs/source-manifest.json  Hashes identifying the source snapshot
validation/test-report.json  Concrete scope and result of the local tests
.github/workflows/tests.yml  Continuous-integration configuration
```
