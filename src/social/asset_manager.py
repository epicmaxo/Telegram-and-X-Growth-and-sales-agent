from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve


class AssetManager:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or os.getenv("ASSET_DIR", "./assets"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def download_mentrast_assets(self) -> dict[str, Any]:
        assets = [
            ("logo", "https://raw.githubusercontent.com/edent/SuperTinyIcons/master/images/svg/rocket.svg"),
            ("favicon", "https://raw.githubusercontent.com/edent/SuperTinyIcons/master/images/svg/globe.svg"),
        ]
        downloaded: list[dict[str, str]] = []
        for name, url in assets:
            destination = self.base_dir / f"{name}.svg"
            try:
                urlretrieve(url, str(destination))
                downloaded.append({"name": name, "path": str(destination)})
            except Exception as exc:  # pragma: no cover - network dependent
                downloaded.append({"name": name, "path": str(destination), "error": str(exc)})
        return {"status": "ready", "assets": downloaded}
