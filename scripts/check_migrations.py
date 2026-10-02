from pathlib import Path
import re
import sys

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
PATTERN = re.compile(r"^(\d{3})_[a-z0-9_]+\.sql$")

files = sorted(p for p in SQL_DIR.glob("*.sql") if PATTERN.match(p.name))
if not files:
    raise SystemExit("No numbered SQL files found.")

numbers = [int(PATTERN.match(p.name).group(1)) for p in files]
expected = list(range(numbers[0], numbers[-1] + 1))

print("SQL checkpoints:")
for p in files:
    print(f"  ✓ {p.name}")

if numbers != expected:
    missing = sorted(set(expected) - set(numbers))
    raise SystemExit(f"Migration/checkpoint numbering gap detected: {missing}")

print("Migration/checkpoint numbering is sequential.")
