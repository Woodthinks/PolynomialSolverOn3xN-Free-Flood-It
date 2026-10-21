# Algorithm notes

## Input, moves, and objective

Let `G` be the complete `3 × n` grid, with `N = 3n` vertices, and let its initial coloring use the palette `{0, 1, 2}`. A move recolors one maximal monochromatic connected component. The pivot can be chosen anywhere on each turn. The optimization objective is the minimum number `F` of moves needed to obtain one monochromatic component.

Rows are supplied top to bottom. Vertex indices in output moves are zero-based and row-major. These conventions apply to every example, test, and public interface.

## Painting representation

The research construction represents a strategy by a rooted painting tree. Each node carries a color and incurs one unit of painting cost. Cells belong to nodes, and ancestor relations describe nested painting regions. The construction uses the identity `P = F + 1` between its minimum painting cost `P` and minimum Free-Flood-It move count `F`.

The extra unit accounts for the initial/root painting stroke. It is why the public `painting_cap` parameter bounds strokes rather than game moves. With no user cap, a greedy strategy supplies a legal bound `F_upper + 1`. Every greedy step merges at least two current components, so it terminates within `N - 1` game moves and gives a painting cap at most `N`.

The implementation's optimization claims rely on the representation theorem and the completeness of the template/frontier construction. Certificate replay checks the recovered upper bound directly; completeness of this representation is a separate mathematical requirement.

## Column templates and connectivity

`polynomial_templates.py` generates small skeletons and bounded alternating chains for one- and two-column windows. `polynomial_solver.py` decorates templates with frontier connectivity and combines successive columns. The templates retain the owners and relevant ancestors of the three frontier vertices.

`frontier.py` computes restrictions and updates of these rooted structures. Connectivity information matters: a set containing the top and bottom frontier vertices can be disconnected even though it has the same owner/ancestor labels as a connected set. For height three, the compiler explicitly considers the exceptional top/bottom chain and its connectivity cutoffs. This is richer than recording only colors or a static terminal-distance table.

The portion of the common-ancestor history omitted from the finite template is represented by a stack. The stack alphabet consists of the three colors plus a bottom marker. A finite control records the column template, its connectivity decoration, and the intermediate states needed to compile transitions.

## Minimum-weight evaluation

`weighted_pushdown.py` evaluates the compiled system by weighted context-free saturation. Summaries record the minimum cost of removing a stack symbol while passing between control states. Rules can have zero cost, so the evaluator must handle productive and nonproductive zero-cost cycles. It keeps derivation witnesses for accepted minima.

`polynomial_solver.py` charges newly created painting nodes, sets up initial and final controls, and extracts the minimum accepted painting cost. Optional spent-cost pruning removes summaries whose accumulated cost and required prefix cost already exceed the cap. The regression suite includes comparisons with pruning disabled.

Neither the compiler nor evaluator enumerates all possible complete stack words. Nevertheless, their explicit finite structures can be large. The research analysis uses a loose `O(N^13)` bound for compiled-system size. Saturation adds work on top of compilation, so this size bound must not be read as a measured or proved `O(N^13)` total runtime for this Python package.

## Recovery and independent replay

`recover_strategy.py` expands the minimum-weight derivation into a painting tree and then produces maximal-component recolorings. The public API runs these moves through a separate grid flood-fill in `api.py`, checks their count against the returned value, and verifies a monochromatic final board.

The replay verifier uses only the input board and the recovered moves. It does not use the pushdown certificate to decide which cells a move recolors. It therefore detects invalid pivots/colors, incorrect component boundaries, incomplete flooding, and count mismatches. It cannot establish that no shorter strategy exists. The tests address that question independently on their small-board sample using exhaustive BFS over legal game states.

## Module map

| Module | Role |
| --- | --- |
| `api.py` | Input checks, public solver, independent replay |
| `polynomial_solver.py` | Template decoration, transition compiler, optimization driver |
| `polynomial_templates.py` | Frontier skeleton and chain generation |
| `frontier.py` | Tree restriction and frontier connectivity updates |
| `weighted_pushdown.py` | Minimum-weight saturation and derivation certificates |
| `recover_strategy.py` | Painting-tree and legal-move recovery |
| `exact.py` | Grid adjacency and monochromatic components used for the greedy bound |
| `__main__.py` | JSON command-line interface |

Despite its historical filename, `exact.py` in this package contains only the two shared graph helpers. The independent exact BFS used for testing lives in `tests/test_solver.py`.
