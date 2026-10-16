import pathlib
import pytest


@pytest.fixture(scope="session")
def repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def read_frontmatter(path: pathlib.Path) -> dict:
    """Parse the YAML-ish frontmatter block of a markdown file into a flat dict.
    Only `key: value` lines are supported; that is all the bundle uses."""
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    end = text.index("\n---", 4)
    block = text[4:end]
    out = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out
