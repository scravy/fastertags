import json
from pathlib import Path

if __name__ == '__main__':
    p = Path(__file__).parent
    f: Path
    for f in p.glob("elements.*.json"):
        t = p / f"normalized.{f.name}"
        if t.exists():
            continue
        with open(f, 'rb') as fp, open(t, 'w') as fq:
            d = json.load(fp)
            d = {k: d[k] for k in sorted(d.keys())}
            json.dump(d, fq, indent=2)
