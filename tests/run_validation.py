"""Run the regression suite and write its concrete scope to a JSON report."""
import json
from pathlib import Path
import platform
import sys
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
started = time.perf_counter()
suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
report = {
    'python': platform.python_version(),
    'suite': 'stdlib unittest; tests/test_solver.py',
    'tests_run': result.testsRun,
    'failures': [{'test': str(test), 'traceback': trace} for test, trace in result.failures],
    'errors': [{'test': str(test), 'traceback': trace} for test, trace in result.errors],
    'skipped': [{'test': str(test), 'reason': reason} for test, reason in result.skipped],
    'successful': result.wasSuccessful(),
    'elapsed_seconds': round(time.perf_counter() - started, 3),
    'optimality_checks': {
        'three_by_two': 'All 122 color-canonical boards over at most three colors',
        'three_by_three': '16 deterministic samples, including 12 generated with seed 94053',
        'three_by_four': '0001 / 2010 / 0101; independent Free optimum 3 and minimum over all 12 Fixed roots 4',
        'method': 'Independent BFS over all legal maximal-component recolorings, modulo color permutation',
    },
    'additional_checks': [
        'Public recovered strategies replay to monochromatic boards',
        'Pruning-disabled run and three palette permutations',
        'Painting-cap limited miss and exact-cap success',
        'Malformed board, cap, and replay-move rejection',
        'JSON CLI success, output-file parity, invalid input, and cap miss',
        'Weighted pushdown zero-cost productive and nonproductive cycles',
    ],
    'limitations': 'Finite small-board regression only; this report is not a proof of general optimality or the claimed asymptotic complexity.',
}
destination = ROOT / 'validation' / 'test-report.json'
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
raise SystemExit(0 if result.wasSuccessful() else 1)
