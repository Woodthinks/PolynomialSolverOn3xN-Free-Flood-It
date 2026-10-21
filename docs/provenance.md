# Provenance and release scope

## Original implementation

The algorithmic implementation originated in round 45 of the surrounding research project, under `research/free_flood_it_3xn/round45/src/`. A later standalone snapshot was kept in `paper_free_flood_it_3xn/code/solver/`. This repository packages that snapshot, which had already removed dependencies on earlier rounds.

All code in this repository was generated entirely by AI, under human direction. This includes the research implementation, release packaging, interfaces, and tests. No independent human code audit is claimed by this statement.

`source-manifest.json` records the original project-relative paths and SHA-256 hashes of the six files used as the packaging source. These are hashes of the original snapshot, not hashes of the modified release files. The original project and manuscript files were left unchanged.

## Packaging changes

The solver modules were moved into the `floodit3` Python package and their imports changed to package-relative imports. Historical script entry points, implicit experiment output locations, and path manipulation were removed. A validated API, JSON CLI, packaging metadata, examples, and GitHub Actions workflow were added. The original `exact.py` was reduced to the grid and component helpers actually used by the main solver.

The optimizer, template generator, frontier updates, weighted pushdown evaluator, and strategy recovery retain the source snapshot's algorithm. Input and witness validation were added around that implementation. This release does not introduce a new theoretical result or a new empirical performance claim.

The public solver requires assertions to remain enabled. It returns recovered legal game moves and independently replays them before reporting success.

## Historical records versus release validation

The surrounding round-45 records report exhaustive color-canonical 3 × 3 comparisons, template-generation audits, weighted-system tests, and additional example families. These records motivated the source selection. They were not regenerated in preparing this repository and their large output files are not included here.

The checks actually run for this release are self-contained in `tests/`, with their scope and result in `validation/test-report.json`. They include independent exact BFS on all color-canonical 3 × 2 boards, a deterministic 3 × 3 sample, and a 3 × 4 Free-versus-Fixed example. They also exercise the public interfaces and weighted evaluator.

Finite tests are regression evidence. They are not a proof of general optimality, the painting representation theorem, or an asymptotic polynomial runtime bound. This repository provides an executable implementation and explicit validation scope so those claims can be assessed separately.
