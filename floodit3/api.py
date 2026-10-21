"""Validated public interface; colors are 0, 1, and 2."""
from .polynomial_solver import solve
from .recover_strategy import recover


def validate_rows(rows):
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be three strings, not one string")
    try:
        rows = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of three strings") from exc
    if len(rows) != 3 or any(not isinstance(row, str) for row in rows):
        raise ValueError("provide exactly three strings")
    if not rows[0] or len({len(row) for row in rows}) != 1:
        raise ValueError("rows must have the same positive width")
    if any(set(row) - set("012") for row in rows):
        raise ValueError("colors must be encoded as 0, 1, or 2")
    return rows


def replay(rows, moves):
    """Replay maximal-component moves independently of the painting certificate.

    Vertices use row-major zero-based indices. Return the final rows.
    Invalid moves raise ValueError; monochromaticity is checked by the caller.
    """
    rows = validate_rows(rows)
    width = len(rows[0])
    state = [int(c) for row in rows for c in row]
    try:
        entries = iter(moves)
    except TypeError as exc:
        raise ValueError("moves must be an iterable of (vertex, color) pairs") from exc
    for entry in entries:
        try:
            vertex, color = entry
        except (TypeError, ValueError) as exc:
            raise ValueError("each move must be a (vertex, color) pair") from exc
        if type(vertex) is not int or not 0 <= vertex < len(state):
            raise ValueError("move vertex is outside the board")
        if type(color) is not int or color not in range(3) or color == state[vertex]:
            raise ValueError("move must change its component to another palette color")
        old = state[vertex]
        reached = {vertex}
        todo = [vertex]
        for u in todo:
            r, c = divmod(u, width)
            for rr, cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if 0 <= rr < 3 and 0 <= cc < width:
                    v = rr*width+cc
                    if v not in reached and state[v] == old:
                        reached.add(v)
                        todo.append(v)
        for u in reached:
            state[u] = color
    return tuple(''.join(str(c) for c in state[r*width:(r+1)*width]) for r in range(3))


def solve_board(rows, *, painting_cap=None, prune=True):
    """Compute a minimum and replay its witness, or report a cap-limited miss.

    painting_cap bounds painting strokes (flooding moves + 1), not moves.
    With no cap, the core uses an input-derived legal upper bound.
    This is research software; successful replay verifies legality, not optimality.
    """
    if not __debug__:
        raise RuntimeError("run without -O: certificate assertions must remain enabled")
    rows = validate_rows(rows)
    if painting_cap is not None and (type(painting_cap) is not int or not 1 <= painting_cap <= 3*len(rows[0])):
        raise ValueError("painting_cap must be an integer from 1 to the number of cells")
    result = solve(rows, cap=painting_cap, witness=True, prune=prune)
    certificate = result.pop('certificate')
    if result['strokes'] is None:
        result.update(status='no_solution_within_cap', moves=None, replay_verified=False)
        return result
    result['strategy'] = recover(rows, certificate, result['strokes'])
    moves = result['strategy']['legal_free_moves']
    final = replay(rows, moves)
    if len(moves) != result['free'] or len(set(''.join(final))) != 1:
        raise RuntimeError("recovered strategy failed independent replay")
    result.update(status='solved', moves=moves, final_rows=final,
                  indexing='row-major, zero-based', replay_verified=True)
    return result
