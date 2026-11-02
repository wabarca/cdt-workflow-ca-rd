import glob, re, os

def scan_all():
    print("Scanning all markdown files in docs/...")
    for f in sorted(glob.glob("docs/*.md")):
        with open(f, "r", encoding="utf-8") as fp:
            content = fp.read()
        blocks = re.findall(r"```mermaid(.*?)```", content, re.DOTALL)
        if blocks:
            for i, b in enumerate(blocks):
                pipe_labels = re.findall(r"\|([^\|]+)\|", b)
                for pl in pipe_labels:
                    stripped = pl.strip()
                    if any(c in stripped for c in ["(", ")", "<", ">", "~", ":"]):
                        if not (stripped.startswith('"') and stripped.endswith('"')):
                            print(f"{f} Block {i+1} problematic pipe: |{stripped}|")

if __name__ == "__main__":
    scan_all()
