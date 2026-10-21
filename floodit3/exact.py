"""Grid adjacency and monochromatic components from the research reference solver."""

def grid(rows, cols):
    adj = [[] for _ in range(rows * cols)]
    for r in range(rows):
        for c in range(cols):
            v = r * cols + c
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    adj[v].append(rr * cols + cc)
    return adj

def components(state, adj):
    unseen = set(range(len(state)))
    answer = []
    while unseen:
        v = min(unseen)
        unseen.remove(v)
        comp = [v]
        for x in comp:
            for y in adj[x]:
                if y in unseen and state[y] == state[v]:
                    unseen.remove(y)
                    comp.append(y)
        answer.append(comp)
    return answer
