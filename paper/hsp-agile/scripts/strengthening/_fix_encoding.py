# -*- coding: utf-8 -*-
from pathlib import Path

root = Path("paper/hsp-agile/scripts/strengthening")
for p in root.glob("*.py"):
    data = p.read_bytes()
    text = data.decode("latin-1")
    text = "".join(ch if ord(ch) < 128 else "?" for ch in text)
    if "coding" not in text[:120]:
        if text.startswith("#!"):
            nl = text.find("\n")
            text = text[: nl + 1] + "# -*- coding: utf-8 -*-\n" + text[nl + 1 :]
        else:
            text = "# -*- coding: utf-8 -*-\n" + text
    p.write_bytes(text.encode("utf-8"))
    print("fixed", p.name)
