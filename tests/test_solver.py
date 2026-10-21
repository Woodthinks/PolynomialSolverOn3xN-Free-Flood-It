"""Small, independent exact checks for the public research solver.

The breadth-first search here enumerates the actual recoloring game; it does
not use the painting representation or the package's component routines.
"""
from collections import deque
from itertools import product
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from floodit3 import replay, solve_board
from floodit3.weighted_pushdown import minimum


ROOT = Path(__file__).resolve().parents[1]


def canonical(state):
    labels = {}
    return tuple(labels.setdefault(color, len(labels)) for color in state)


def neighbors(state, width, fixed_root=None):
    """Generate every legal maximal-component recoloring, modulo color names."""
    unseen = set(range(len(state)))
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        queue = [start]
        for u in queue:
            row, col = divmod(u, width)
            candidates = []
            if row:
                candidates.append(u - width)
            if row < 2:
                candidates.append(u + width)
            if col:
                candidates.append(u - 1)
            if col + 1 < width:
                candidates.append(u + 1)
            for v in candidates:
                if v in unseen and state[v] == state[start]:
                    unseen.remove(v)
                    component.add(v)
                    queue.append(v)
        if fixed_root is not None and fixed_root not in component:
            continue
        for target in range(3):
            if target != state[start]:
                result = list(state)
                for v in component:
                    result[v] = target
                yield canonical(result)


def bfs_distance(rows, fixed_root=None):
    width = len(rows[0])
    start = canonical(tuple(int(c) for row in rows for c in row))
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        state, distance = queue.popleft()
        if len(set(state)) == 1:
            return distance
        for following in neighbors(state, width, fixed_root):
            if following not in seen:
                seen.add(following)
                queue.append((following, distance + 1))
    raise AssertionError("a connected nonempty grid must be floodable")


def rows_from_state(state, width):
    return tuple(''.join(str(c) for c in state[r * width:(r + 1) * width])
                 for r in range(3))


class SolverOptimalityTests(unittest.TestCase):
    def assert_solution(self, rows, expected, **options):
        result = solve_board(rows, **options)
        self.assertEqual(result['status'], 'solved')
        self.assertEqual(result['free'], expected)
        self.assertEqual(result['strokes'], expected + 1)
        self.assertEqual(len(result['moves']), expected)
        self.assertTrue(result['replay_verified'])
        final = replay(rows, result['moves'])
        self.assertEqual(final, result['final_rows'])
        self.assertEqual(len(set(''.join(final))), 1)
        return result

    def test_all_color_canonical_three_by_two_boards(self):
        boards = [state for state in product(range(3), repeat=6)
                  if canonical(state) == state]
        self.assertEqual(len(boards), 122)
        for state in boards:
            rows = rows_from_state(state, 2)
            with self.subTest(rows=rows):
                self.assert_solution(rows, bfs_distance(rows))

    def test_three_by_three_samples(self):
        rng = random.Random(94053)
        samples = {
            ('000', '000', '000'),
            ('012', '120', '201'),
            ('010', '121', '010'),
            ('012', '012', '012'),
        }
        while len(samples) < 16:
            samples.add(rows_from_state(canonical(tuple(rng.randrange(3) for _ in range(9))), 3))
        self.assertEqual(len(samples), 16)
        for rows in sorted(samples):
            with self.subTest(rows=rows):
                self.assert_solution(rows, bfs_distance(rows))

    def test_free_moves_can_outperform_every_fixed_root(self):
        rows = ('0001', '2010', '0101')
        self.assertEqual(bfs_distance(rows), 3)
        fixed_values = [bfs_distance(rows, root) for root in range(12)]
        self.assertEqual(min(fixed_values), 4)
        self.assert_solution(rows, 3)

    def test_pruning_disabled_and_color_permutations(self):
        rows = ('012', '210', '102')
        expected = bfs_distance(rows)
        self.assert_solution(rows, expected, prune=False)
        for image in ('120', '201', '210'):
            translation = str.maketrans('012', image)
            recolored = tuple(row.translate(translation) for row in rows)
            with self.subTest(image=image):
                self.assert_solution(recolored, expected)

    def test_painting_cap_is_one_more_than_move_limit(self):
        rows = ('01', '20', '12')
        expected = bfs_distance(rows)
        self.assertEqual(expected, 3)
        missed = solve_board(rows, painting_cap=expected)
        self.assertEqual(missed['status'], 'no_solution_within_cap')
        self.assertIsNone(missed['strokes'])
        self.assertIsNone(missed['free'])
        self.assertIsNone(missed['moves'])
        self.assertFalse(missed['replay_verified'])
        self.assert_solution(rows, expected, painting_cap=expected + 1)
        self.assert_solution(('0', '0', '0'), 0, painting_cap=1)


class PublicInterfaceTests(unittest.TestCase):
    def test_replay_recolors_only_the_selected_maximal_component(self):
        rows = ('010', '010', '010')
        self.assertEqual(replay(rows, [(0, 2)]), ('210', '210', '210'))
        self.assertEqual(replay(rows, [(0, 1)]), ('110', '110', '110'))
        self.assertEqual(replay(rows, [(0, 1), (4, 0)]), ('000', '000', '000'))

    def test_malformed_boards(self):
        invalid = [None, '012', b'012', (), ('0', '0'), ('0',) * 4,
                   ('', '', ''), ('0', '01', '0'), ('0', 0, '0'),
                   ('3', '0', '0'), ('a', 'b', 'c'), ('0 ', '01', '00')]
        for rows in invalid:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                solve_board(rows)
        for cap in (0, -1, 4, 1.0, True, '1'):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                solve_board(('0', '1', '2'), painting_cap=cap)

    def test_invalid_replay_moves(self):
        for move in ((-1, 1), (3, 1), (False, 1), (0, 0), (0, 3),
                     (0, True), (0, '1'), (), (0,), (0, 1, 2), 0, None):
            with self.subTest(move=move), self.assertRaises(ValueError):
                replay(('0', '0', '0'), [move])
        for moves in (None, 1, False):
            with self.subTest(moves=moves), self.assertRaises(ValueError):
                replay(('0', '0', '0'), moves)

    def test_cli_emits_one_json_document_and_saves_same_payload(self):
        with tempfile.TemporaryDirectory(prefix='floodit3-test-', dir=Path(__file__).parent) as temp:
            output = Path(temp) / 'result.json'
            command = [sys.executable, '-m', 'floodit3', '--rows', '01', '20', '12',
                       '--output', str(output)]
            completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload, json.loads(output.read_text(encoding='utf-8')))
            self.assertEqual(payload['status'], 'solved')
            self.assertEqual(payload['free'], 3)
            self.assertEqual(completed.stderr, '')
            final = replay(('01', '20', '12'), payload['moves'])
            self.assertEqual(len(set(''.join(final))), 1)

    def test_cli_invalid_input_and_cap_miss(self):
        base = [sys.executable, '-m', 'floodit3', '--rows']
        invalid = subprocess.run(base + ['03', '00', '00'], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(invalid.returncode, 2)
        self.assertIn('colors must be encoded', invalid.stderr)
        capped = subprocess.run(base + ['01', '20', '12', '--painting-cap', '3'],
                                cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(capped.stdout)['status'], 'no_solution_within_cap')


class WeightedPushdownTests(unittest.TestCase):
    def test_zero_cost_cycles_do_not_replace_the_finite_witness(self):
        rules = [
            (0, 'Z', 0, ('Z',), 0),
            (0, 'Z', 0, ('A', 'B'), 0),
            (0, 'A', 0, ('A',), 0),
            (0, 'A', 1, (), 1),
            (1, 'B', 1, ('B',), 0),
            (1, 'B', 2, (), 2),
            (0, 'Z', 2, (), 7),
        ]
        value, stats = minimum(rules, 0, 'Z', 2, 10, witness=True)
        self.assertEqual(value, 3)
        self.assertEqual(stats['trace'], [1, 3, 5])
        state, stack, spent = 0, ['Z'], 0
        for index in stats['trace']:
            p, symbol, target, word, cost = rules[index]
            self.assertEqual(state, p)
            self.assertEqual(stack.pop(), symbol)
            stack.extend(reversed(word))
            state = target
            spent += cost
        self.assertEqual((state, stack, spent), (2, [], 3))
        missed, stats = minimum(rules, 0, 'Z', 2, 2, witness=True)
        self.assertGreater(missed, 2)
        self.assertIsNone(stats['trace'])

    def test_nonproductive_zero_cycle_is_not_an_accepting_run(self):
        value, stats = minimum([(0, 'Z', 0, ('Z',), 0)], 0, 'Z', 1, 4, witness=True)
        self.assertGreater(value, 4)
        self.assertIsNone(stats['trace'])


if __name__ == '__main__':
    unittest.main()
