import os
import re
import glob

def replace_terms_in_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    orig = content

    # Replace "pipeline" variations
    # "un pipeline" -> "una secuencia de procesamiento"
    content = re.sub(r'\bel\s+pipeline\b', 'la secuencia de procesamiento', content, flags=re.I)
    content = re.sub(r'\bun\s+pipeline\b', 'una secuencia de procesamiento', content, flags=re.I)
    content = re.sub(r'\bdel\s+pipeline\b', 'de la secuencia de procesamiento', content, flags=re.I)
    content = re.sub(r'\bal\s+pipeline\b', 'a la secuencia de procesamiento', content, flags=re.I)
    content = re.sub(r'\beste\s+pipeline\b', 'esta secuencia de procesamiento', content, flags=re.I)
    content = re.sub(r'\btodo\s+el\s+pipeline\b', 'toda la secuencia de procesamiento', content, flags=re.I)
    content = re.sub(r'\bpipelines\b', 'secuencias de procesamiento', content, flags=re.I)
    content = re.sub(r'\bpipeline\b', 'secuencia de procesamiento', content, flags=re.I)

    # Replace "cribado" variations
    # "cribado exploratorio" -> "evaluación exploratoria preliminar"
    content = re.sub(r'\bcribado\s+exploratorio\b', 'evaluación exploratoria preliminar', content, flags=re.I)
    content = re.sub(r'\bfase\s+de\s+cribado\b', 'fase exploratoria preliminar', content, flags=re.I)
    content = re.sub(r'\betapa\s+de\s+cribado\b', 'etapa exploratoria preliminar', content, flags=re.I)
    content = re.sub(r'\bcribados\b', 'evaluaciones preliminares', content, flags=re.I)
    content = re.sub(r'\bcribado\b', 'evaluación preliminar', content, flags=re.I)

    if content != orig:
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"Updated terms in: {filepath}")

def run():
    all_files = glob.glob("docs/*.md") + glob.glob("docs-private/*.md")
    for f in all_files:
        replace_terms_in_file(f)

if __name__ == "__main__":
    run()
