"""Direct polynomial template generation for a fixed-size connected window.

Subset/partition enumeration is only over at most 2*h window positions.
Long chains are generated as alternating words, never as arbitrary trees.
"""
from functools import lru_cache
from itertools import product


def partitions(items):
    if not items:
        yield ()
        return
    first, *rest = items
    for part in partitions(rest):
        yield ((first,),) + part
        for i in range(len(part)):
            yield part[:i] + ((first,) + part[i],) + part[i+1:]


@lru_cache(None)
def templates(pattern, h, bound):
    k = len(pattern)
    nb = [0] * k
    for j in range(k // h):
        for r in range(h-1):
            a, b = j*h+r, j*h+r+1
            nb[a] |= 1 << b
            nb[b] |= 1 << a
    if k == 2*h:
        for r in range(h):
            nb[r] |= 1 << (h+r)
            nb[h+r] |= 1 << r
    assert k in (h, 2*h)
    full = (1 << k)-1
    cm = [sum(1 << v for v, c in enumerate(pattern) if c == a) for a in range(3)]

    @lru_cache(None)
    def allowed(mask):
        border = 0
        for v in range(k):
            if mask >> v & 1:
                border |= nb[v]
        border &= ~mask
        return tuple(c for c in range(3) if not (cm[c] & border))

    def components(mask):
        out = []
        while mask:
            comp = mask & -mask
            while True:
                grown = comp
                for v in range(k):
                    if comp >> v & 1:
                        grown |= nb[v] & mask
                if grown == comp:
                    break
                comp = grown
            mask &= ~comp
            out.append(comp)
        return tuple(out)

    @lru_cache(None)
    def skeletons(mask):
        result = set()
        for c in allowed(mask):
            available = mask & cm[c]
            keep = available
            while True:
                for part in partitions(components(mask ^ keep)):
                    child_masks = tuple(sorted((sum(block) for block in part), key=lambda m: (m & -m)))
                    if not keep and len(child_masks) < 2:
                        continue
                    for children in product(*(skeletons(m) for m in child_masks)):
                        result.add((c, keep, tuple(children)))
                if keep == 0:
                    break
                keep = (keep-1) & available
        return tuple(sorted(result))

    found = set()
    for tree in skeletons(full):
        nodes, children, domain = [], [], []
        def flatten(t):
            color, marks, kids = t
            x = len(nodes)
            nodes.append((color, marks))
            children.append([])
            domain.append(marks)
            for child in kids:
                y = flatten(child)
                children[x].append(y)
                domain[x] |= domain[y]
            return x
        flatten(tree)
        if len(nodes) > bound:
            continue
        edge_order = [(p, ch) for p, kids in enumerate(children) for ch in kids]
        choices = []
        for p, ch in edge_order:
            a, b = nodes[p][0], nodes[ch][0]
            palette = allowed(domain[ch])
            assert len(palette) <= 2
            words = [()] if a != b else []
            max_length = bound-len(nodes)
            if len(palette) == 1:
                q = palette[0]
                if max_length and a != q and b != q:
                    words.append((q,))
            elif len(palette) == 2:
                for first in palette:
                    other = next(c for c in palette if c != first)
                    for length in range(1, max_length+1):
                        word = tuple(first if i % 2 == 0 else other for i in range(length))
                        if word[0] != a and word[-1] != b:
                            words.append(word)
            choices.append(tuple(words))

        def emit(words):
            chain = dict(zip(edge_order, words))
            parent, colors, owners = [], [], [None]*k
            def visit(x, p):
                me = len(parent)
                parent.append(p)
                colors.append(nodes[x][0])
                for v in range(k):
                    if nodes[x][1] >> v & 1:
                        owners[v] = me
                for ch in children[x]:
                    last = me
                    for c in chain[x, ch]:
                        now = len(parent)
                        parent.append(last)
                        colors.append(c)
                        last = now
                    visit(ch, last)
            visit(0, -1)
            assert all(x is not None for x in owners)
            found.add((tuple(parent), tuple(colors), tuple(owners)))

        def fill(i, remaining, words):
            if i == len(choices):
                emit(words)
                return
            for word in choices[i]:
                if len(word) <= remaining:
                    fill(i+1, remaining-len(word), words+(word,))
        fill(0, bound-len(nodes), ())
    return tuple(sorted(found))
