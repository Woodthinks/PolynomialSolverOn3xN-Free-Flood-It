"""Reconstruct global node identities and legal Free moves from PDA metadata."""
from .frontier import restrict
from .exact import grid, components


def recover(rows, certificate, strokes):
    n = len(rows[0])
    parents, colors, stack = [], [], []
    owners = [None] * (3*n)
    finite_ids, current = None, None

    def create(color, parent):
        me = len(parents)
        assert parent < me
        parents.append(parent)
        colors.append(color)
        return me

    for item in certificate:
        if item[0] == 'initial_ancestor':
            stack.append(create(item[1], stack[-1] if stack else -1))
        elif item[0] == 'initial_frontier':
            current = item[1]
            par, col, own = current
            finite_ids = []
            for x, c in enumerate(col):
                p = finite_ids[par[x]] if par[x] >= 0 else (stack[-1] if stack else -1)
                finite_ids.append(create(c, p))
            owners[:3] = [finite_ids[x] for x in own]
        else:
            _, j, joint = item
            par, col, own = joint
            old, old_ids, pop, anc = restrict(par, col, own, (0, 1, 2))
            new, new_ids, push, _ = restrict(par, col, own, (3, 4, 5))
            assert old == current
            gids = {x: finite_ids[k] for x, k in old_ids.items()}
            oldroot = next(x for x, i in old_ids.items() if i == 0)
            prefix_nodes = anc[oldroot][:-1]
            assert len(prefix_nodes) == len(pop)
            if pop:
                suffix = stack[-len(pop):]
                assert tuple(colors[x] for x in suffix) == pop
                gids.update(zip(prefix_nodes, suffix))
                stack = stack[:-len(pop)]
            for x, c in enumerate(col):
                if x not in gids:
                    assert par[x] >= 0
                    gids[x] = create(c, gids[par[x]])
                else:
                    expected_parent = gids[par[x]] if par[x] >= 0 else (stack[-1] if stack else -1)
                    assert parents[gids[x]] == expected_parent
                    assert colors[gids[x]] == c
            assert owners[3*j:3*j+3] == [gids[x] for x in own[:3]]
            owners[3*(j+1):3*(j+2)] = [gids[x] for x in own[3:]]
            finite_ids = [None]*len(new_ids)
            for x, i in new_ids.items():
                finite_ids[i] = gids[x]
            newroot = next(x for x, i in new_ids.items() if i == 0)
            stack += [gids[x] for x in anc[newroot][:-1]]
            current = new
    assert len(parents) == strokes and all(x is not None for x in owners)
    assert parents.count(-1) == 1
    areas = [set() for _ in parents]
    for cm, x in enumerate(owners):
        row, column = cm % 3, cm // 3
        v = row*n + column
        assert colors[x] == int(rows[row][column])
        while x >= 0:
            areas[x].add(v)
            x = parents[x]
    adj = grid(3, n)
    for area in areas:
        assert area
        reached = {min(area)}
        todo = list(reached)
        for u in todo:
            for v in adj[u]:
                if v in area and v not in reached:
                    reached.add(v)
                    todo.append(v)
        assert reached == area
    plan = [dict(color=c, cells=sorted(area)) for area, c in zip(areas, colors)]
    # Direct-reversal lemma: each region is exactly the current component.
    # This checks the emitted tree itself, without repairing its regions.
    trace = []
    state = tuple(map(int, ''.join(rows)))
    for x in range(strokes-1, 0, -1):
        area = areas[x]
        v = min(area)
        c = colors[parents[x]]
        block = set(next(b for b in components(state, adj) if v in b))
        assert block == area, ('nonmaximal reconstructed region', x, block, area)
        assert state[v] == colors[x] != c
        state = tuple(c if u in area else d for u, d in enumerate(state))
        trace.append((v, c))
    assert len(set(state)) == 1
    return dict(parents=parents, colors=colors, owners_column_major=owners,
                plan=plan, legal_free_moves=trace, painting_normalizations=0)
