"""Command-line entry point. Writes a single JSON document."""
import argparse
import json
from pathlib import Path
from .api import solve_board


def main():
    parser = argparse.ArgumentParser(description="Research solver: three-color complete 3 x n Free-Flood-It")
    parser.add_argument('--rows', nargs=3, required=True, metavar=('TOP', 'MIDDLE', 'BOTTOM'))
    parser.add_argument('--painting-cap', type=int, help="maximum painting strokes (moves + 1)")
    parser.add_argument('--no-prune', action='store_true', help="disable spent-cost pruning")
    parser.add_argument('--output', type=Path, help="also save the JSON result to this file")
    args = parser.parse_args()
    try:
        result = solve_board(args.rows, painting_cap=args.painting_cap, prune=not args.no_prune)
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    payload = json.dumps(result, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8')
    print(payload, end='')


if __name__ == '__main__':
    main()
