import os, json, re
from datetime import datetime

POSTS_DIR = "posts"
OUT_FILE = "index.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.search(text)
    if not m:
        raise ValueError("Missing frontmatter block (--- ... ---)")

    raw = m.group(1)
    lines = raw.splitlines()

    data = {}
    current_obj = None

    def parse_value(v: str):
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        if v.startswith("'") and v.endswith("'"):
            return v[1:-1]
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            if not inner:
                return []
            parts = [p.strip() for p in inner.split(",")]
            out = []
            for p in parts:
                p = p.strip()
                if (p.startswith('"') and p.endswith('"')) or (p.startswith("'") and p.endswith("'")):
                    out.append(p[1:-1])
                else:
                    out.append(p)
            return out
        if v.lower() in ("true", "false"):
            return v.lower() == "true"
        return v

    for line in lines:
        if not line.strip():
            continue

        # Start nested object: e.g., media:
        if re.match(r"^[a-zA-Z0-9_]+:\s*$", line) and not line.startswith("  "):
            key = line.split(":")[0].strip()
            data[key] = {}
            current_obj = key
            continue

        # Nested key (two spaces indent)
        if current_obj and line.startswith("  "):
            k, _, v = line.strip().partition(":")
            data[current_obj][k.strip()] = parse_value(v)
            continue

        # Regular key
        k, _, v = line.partition(":")
        data[k.strip()] = parse_value(v)

    return data

def main():
    posts = []
    for fname in os.listdir(POSTS_DIR):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(POSTS_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        fm = parse_frontmatter(text)

        required = ["title", "date", "type", "tags", "excerpt", "slug"]
        missing = [k for k in required if k not in fm or fm[k] in (None, "", [])]
        if missing:
            raise ValueError(f"{fname} missing required fields: {missing}")

        # Validate date format
        try:
            datetime.strptime(fm["date"], "%Y-%m-%d")
        except Exception:
            raise ValueError(f"{fname} has invalid date format. Use YYYY-MM-DD.")

        item = {
            "title": fm["title"],
            "date": fm["date"],
            "type": fm["type"],
            "tags": fm["tags"],
            "excerpt": fm["excerpt"],
            "slug": fm["slug"],
            "thumbnail": fm.get("thumbnail", "") or "",
            "media": fm.get("media", {"kind": "none", "youtube_id": "", "images": []}),
            "url": f"/blog/{fm['slug']}"
        }

        posts.append(item)

    # Sort newest first
    posts.sort(key=lambda x: x["date"], reverse=True)

    out = {"posts": posts}

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT_FILE} with {len(posts)} posts.")

if __name__ == "__main__":
    main()
