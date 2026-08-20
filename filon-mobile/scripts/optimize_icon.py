from pathlib import Path
from PIL import Image

root = Path("/home/ubuntu/filon-mobile/assets/images")
source = root / "icon.png"

targets = {
    "icon.png": 512,
    "splash-icon.png": 512,
    "favicon.png": 96,
    "android-icon-foreground.png": 512,
}

with Image.open(source) as original:
    rgb = original.convert("RGB")
    for filename, size in targets.items():
        asset = rgb.resize((size, size), Image.Resampling.LANCZOS)
        asset.save(root / filename, format="PNG", optimize=True, compress_level=9)
