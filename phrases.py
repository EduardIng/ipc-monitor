import os
import re

_PHRASES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phrases.md")


def load_phrases():
    """Parse numbered phrases from phrases.md."""
    phrases = []
    with open(_PHRASES_FILE, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\d+\.\s+(.+)", line.strip())
            if m:
                phrases.append(m.group(1))
    return phrases
