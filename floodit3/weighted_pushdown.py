"""Sparse nonnegative integer min-plus saturation of a weighted PDA.

Rule (p,A,r,word,w) replaces stack top A by word (leftmost is top).
words have length at most two. Costs above cap are discarded.
No explicit stack contents are enumerated.
"""
from collections import defaultdict
from heapq import heappush, heappop


def minimum(rules, start, bottom, finish, cap, witness=False, prefix_floor=None):
    unary = defaultdict(list)
    binary = defaultdict(list)
    d = defaultdict(dict)
    proof = {}
    pending = []
    settled = defaultdict(dict)
    waiting = defaultdict(dict)
    relaxations = 0
    prefix_floor = {} if prefix_floor is None else prefix_floor

    def improve(key, end, value, cert):
        nonlocal relaxations
        if value + prefix_floor.get(key, 0) <= cap and value < d[key].get(end, cap+1):
            assert end not in settled[key], 'a finalized minimum improved'
            d[key][end] = value
            if witness:
                proof[key, end] = cert
            heappush(pending, (value, key, end))
            relaxations += 1

    for rid, (p, a, r, word, w) in enumerate(rules):
        assert len(word) <= 2 and w >= 0
        if not word:
            improve((p, a), r, w, (rid, ()))
        elif len(word) == 1:
            unary[r, word[0]].append((p, a, w, rid))
        else:
            binary[r, word[0]].append((p, a, word[1], w, rid))

    while pending:
        val, key, end = heappop(pending)
        if d[key].get(end) != val or end in settled[key]:
            continue
        settled[key][end] = val
        if key == (start, bottom) and end == finish:
            break
        cp = proof[key, end] if witness else None
        for p, a, w, rid in unary.get(key, ()):
            improve((p, a), end, w+val, (rid, (cp,)))
        # This settled/improved item is the first child of a binary rule.
        for p, a, c, w, rid in binary.get(key, ()):
            base = w+val
            if base > cap:
                continue
            childkey = end, c
            ident = p, a, rid
            old = waiting[childkey].get(ident)
            if old is not None and old[0] <= base:
                continue
            waiting[childkey][ident] = base, cp
            for q, tail in tuple(settled[childkey].items()):
                tailproof = proof[childkey, q] if witness else None
                improve((p, a), q, base+tail, (rid, (cp, tailproof)))
        # This item is the second child of any previously matched rule.
        for (p, a, rid), (base, firstproof) in tuple(waiting.get(key, {}).items()):
            improve((p, a), end, base+val, (rid, (firstproof, cp)))

    val = d[start, bottom].get(finish, cap+1)
    trace = None
    if witness and val <= cap:
        trace = []
        agenda = [proof[(start, bottom), finish]]
        while agenda:
            rid, children = agenda.pop()
            trace.append(rid)
            agenda.extend(reversed(children))
        # Independently execute the extracted transition sequence.
        state, stack, cost = start, [bottom], 0
        for rid in trace:
            p, a, r, word, w = rules[rid]
            assert cost >= prefix_floor.get((p, a), 0)
            assert state == p and stack.pop() == a
            stack.extend(reversed(word))
            state, cost = r, cost+w
        assert state == finish and not stack and cost == val
    return val, dict(variables=sum(map(len, d.values())), relaxations=relaxations,
                     settled_variables=sum(map(len, settled.values())),
                     binary_matches=sum(map(len, waiting.values())), trace=trace)
