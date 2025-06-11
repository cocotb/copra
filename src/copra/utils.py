from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any


def dump_pickle(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        pickle.dump(obj, fh)


def load_pickle(path: Path) -> Any:
    with path.open("rb") as fh:
        return pickle.load(fh)
