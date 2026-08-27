"""
Ersatter CREATURE_DB-konstanten i index.html med innehallet i
data/creatures_db.json. Kor detta efter varje gang build_palette_db.py
har byggt en ny databas.

Anvandning (fran projektets rotmapp):
    python scripts/inline_db.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
db_path = ROOT / "data" / "creatures_db.json"
html_path = ROOT / "index.html"

db = json.loads(db_path.read_text(encoding="utf-8"))
inline = json.dumps(db, ensure_ascii=False)

html = html_path.read_text(encoding="utf-8")
new_html, n = re.subn(
    r"const CREATURE_DB = .*?;",
    f"const CREATURE_DB = {inline};",
    html,
    count=1,
    flags=re.DOTALL,
)

if n == 0:
    raise SystemExit("Hittade ingen 'const CREATURE_DB = ...;' rad att ersatta i index.html")

html_path.write_text(new_html, encoding="utf-8")
print(f"Klart. {len(db)} monster inbakade i index.html ({len(inline)} bytes JSON).")