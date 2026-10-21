from collections import defaultdict

def restrict(parent, colors, owners, labels):
    anc = []
    for x, p in enumerate(parent):
        anc.append((anc[p] if p >= 0 else ()) + (x,))
    common = set(anc[owners[labels[0]]])
    for v in labels[1:]:
        common &= set(anc[owners[v]])
    root = max(common, key=lambda x: len(anc[x]))
    keep = set().union(*(set(anc[owners[v]]) for v in labels)) - set(anc[root][:-1])
    children = defaultdict(list)
    for x in keep:
        if x != root:
            children[parent[x]].append(x)
    def key(x):
        return min(i for i, v in enumerate(labels) if x in anc[owners[v]])
    order = []
    def visit(x):
        order.append(x)
        for ch in sorted(children[x], key=key):
            visit(ch)
    visit(root)
    ids = {x: i for i, x in enumerate(order)}
    signature = (tuple(-1 if x == root else ids[parent[x]] for x in order),
                 tuple(colors[x] for x in order), tuple(ids[owners[v]] for v in labels))
    prefix = tuple(colors[x] for x in anc[root][:-1])
    return signature, ids, prefix, tuple(anc)

def update(joint, old_rho, old_ids, h):
    par, colors, owners = joint
    _, new_ids, push, anc = restrict(par, colors, owners, tuple(range(h, 2 * h)))
    old_anc = set().union(*(set(anc[owners[v]]) for v in range(h)))
    new_anc = set().union(*(set(anc[owners[v]]) for v in range(h, 2 * h)))
    outputs = {}
    for x in range(len(par)):
        verts = [v for v in range(2 * h) if x in anc[owners[v]]]
        ds = {v: v for v in verts}
        def find(v):
            while ds[v] != v:
                v = ds[v]
            return v
        def merge(a, b):
            ds[find(a)] = find(b)
        if x in old_ids:
            for block in old_rho[old_ids[x]]:
                for v in block[1:]:
                    merge(block[0], v)
        elif x in old_anc:
            for v in range(1, h):
                merge(0, v)
        for v in range(h, 2 * h):
            if v not in ds:
                continue
            if v - h in ds:
                merge(v, v - h)
            if v + 1 < 2 * h and v + 1 in ds:
                merge(v, v + 1)
        blocks = defaultdict(list)
        for v in verts:
            blocks[find(v)].append(v)
        kept = tuple(sorted(tuple(v - h for v in block if v >= h) for block in blocks.values()))
        if x in new_anc:
            if any(not block for block in kept):
                return None
            if x in new_ids:
                outputs[new_ids[x]] = kept
            elif len(kept) != 1 or kept[0] != tuple(range(h)):
                return None
        elif len(blocks) != 1:
            return None
    return tuple(outputs[x] for x in range(len(outputs))), len(par) - len(old_anc)
