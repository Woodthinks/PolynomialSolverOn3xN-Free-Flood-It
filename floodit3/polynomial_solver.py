"""Compiled polynomial solver for complete three-colored height-three strips.

Uses polynomial small skeletons and alternating chains, finite frontier
partitions, and weighted PDA saturation. It never enumerates stack words.
"""
from itertools import product
from collections import defaultdict
import time

from .frontier import restrict, update
from .polynomial_templates import templates
from .weighted_pushdown import minimum


def legal_upper_bound(rows):
    """An input-computed upper bound, not an optimum oracle."""
    from .exact import grid, components
    s = tuple(map(int, ''.join(rows)))
    adj = grid(3, len(rows[0]))
    trace = []
    while len(set(s)) > 1:
        blocks = components(s, adj)
        ids = {v: i for i, b in enumerate(blocks) for v in b}
        best = None
        for block in blocks:
            for c in range(3):
                if c == s[block[0]]:
                    continue
                merges = {ids[v] for u in block for v in adj[u] if s[v] == c}
                if merges and (best is None or len(merges) > best[0]):
                    best = len(merges), block, c
        assert best is not None
        _, block, c = best
        trace.append((block[0], c))
        active = set(block)
        s = tuple(c if v in active else a for v, a in enumerate(s))
    return len(trace)+1, trace


def decorations(t):
    """For three rows, only domain {top,bottom} can be disconnected.

    Such nodes form one chain. Its partition changes at most once.
    """
    p, c, owners = t
    _, _, _, anc = restrict(p, c, owners, (0, 1, 2))
    domains = [tuple(v for v in range(3) if x in anc[owners[v]]) for x in range(len(p))]
    exceptional = [x for x, domain in enumerate(domains) if domain == (0, 2)]
    for a, b in zip(exceptional, exceptional[1:]):
        assert a in anc[b]
    for cutoff in range(len(exceptional)+1):
        separated = set(exceptional[cutoff:])
        yield tuple(((0,), (2,)) if x in separated else (domain,) for x, domain in enumerate(domains))


def solve(rows, cap=None, witness=True, prune=True):
    assert len(rows) == 3 and len(set(map(len, rows))) == 1 and len(rows[0]) > 0
    assert set(''.join(rows)) <= set('012')
    n, N = len(rows[0]), 3*len(rows[0])
    if cap is None:
        cap, upper_trace = legal_upper_bound(rows)
    else:
        upper_trace = None
    assert 1 <= cap <= N
    begin = time.monotonic()
    columns = [tuple(int(rows[r][j]) for r in range(3)) for j in range(n)]
    rules, metadata = [], []
    next_state = 0
    floors = {}
    def fresh(paid_floor=0):
        nonlocal next_state
        x = next_state
        next_state += 1
        for a in range(4):
            floors[x, a] = paid_floor
        return x
    start, end, cleanup = fresh(), fresh(), fresh()
    bottom = 3
    alphabet = tuple(range(4))
    for a in range(3):
        floors[start, a] = 1
    def add(p, a, r, word, cost=0, meta=None):
        rules.append((p, a, r, tuple(word), cost))
        metadata.append(meta)
    # Initialization guesses common ancestors, charging once per new node.
    for a in alphabet:
        for c in range(3):
            if c != a:
                add(start, a, start, (c, a), 1, ('initial_ancestor', c))
    controls = []
    for pattern in columns:
        layer = {}
        for t in templates(pattern, 3, cap):
            for rho in decorations(t):
                q = fresh(len(t[0]))
                for a in range(3):
                    floors[q, a] += 1
                layer[t, rho] = q
        controls.append(layer)
    for (t, rho), q in controls[0].items():
        p, c, own = t
        _, _, _, anc = restrict(p, c, own, (0, 1, 2))
        expected = []
        for x in range(len(p)):
            domain = [v for v in range(3) if x in anc[own[v]]]
            parts = []
            for v in domain:
                if parts and parts[-1][-1] == v-1:
                    parts[-1].append(v)
                else:
                    parts.append([v])
            expected.append(tuple(map(tuple, parts)))
        if tuple(expected) == rho:
            for a in alphabet:
                if a != c[0]:
                    add(start, a, q, (a,), len(p), ('initial_frontier', t))
    macros = 0
    for j in range(n-1):
        old_index = defaultdict(list)
        for (old, rho), q in controls[j].items():
            old_index[old].append((rho, q))
        for joint in templates(columns[j]+columns[j+1], 3, cap):
            p, c, own = joint
            old, ids, pop, _ = restrict(p, c, own, (0, 1, 2))
            new, _, push, _ = restrict(p, c, own, (3, 4, 5))
            for rho, source in old_index.get(old, ()):
                rec = update(joint, rho, ids, 3)
                if rec is None:
                    continue
                newrho, extra = rec
                target = controls[j+1].get((new, newrho))
                assert target is not None, 'partition compression omitted a valid state'
                macros += 1
                at = fresh(len(p))
                for a in alphabet:
                    add(source, a, at, (a,), extra, ('macro', j, joint))
                for c in reversed(pop):
                    to = fresh(len(p))
                    add(at, c, to, ())
                    at = to
                for c in push:
                    to = fresh(len(p))
                    for a in alphabet:
                        add(at, a, to, (c, a))
                    at = to
                for a in alphabet:
                    add(at, a, target, (a,))
    for (t, rho), q in controls[-1].items():
        if all(len(blocks) == 1 for blocks in rho):
            for a in alphabet:
                add(q, a, cleanup, (a,))
    for a in range(3):
        add(cleanup, a, cleanup, ())
    add(cleanup, bottom, end, ())
    compiled = time.monotonic()
    value, info = minimum(rules, start, bottom, end, cap, witness=witness,
                          prefix_floor=floors if prune else None)
    trace = info.pop('trace')
    cert = [metadata[r] for r in trace if metadata[r] is not None] if trace is not None else None
    return dict(rows=rows, cap=cap, strokes=value if value <= cap else None,
                free=value-1 if value <= cap else None, controls=next_state,
                transitions=len(rules), macros=macros, finite_states=[len(layer) for layer in controls],
                grammar=info, compilation_seconds=compiled-begin,
                seconds=time.monotonic()-begin, certificate=cert,
                upper_bound_source='legal_greedy_strategy' if upper_trace is not None else 'supplied_cap',
                upper_bound_moves=upper_trace, spent_cost_pruning=prune)
