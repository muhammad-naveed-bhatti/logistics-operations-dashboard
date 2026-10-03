from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "supabase" / "migrations"
PATTERN = re.compile(r"^(\d{14})_[a-z0-9_]+\.sql$")

files = sorted(MIGRATIONS_DIR.glob("*.sql"))
if not files:
    raise SystemExit("No Supabase migration files found.")

versions = []
for path in files:
    match = PATTERN.match(path.name)
    if not match:
        raise SystemExit(f"Invalid Supabase migration filename: {path.name}")
    versions.append(match.group(1))

if len(versions) != len(set(versions)):
    raise SystemExit("Duplicate Supabase migration version detected.")

if versions != sorted(versions):
    raise SystemExit("Supabase migrations are not in chronological order.")

print("Supabase migration history:")
for path in files:
    print(f"  ✓ {path.name}")

print(f"Validated {len(files)} timestamped migration files.")
