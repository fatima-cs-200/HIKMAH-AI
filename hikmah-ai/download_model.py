"""
Robust model downloader with resume support.
Run: python download_model.py
"""
import truststore, ssl
truststore.inject_into_ssl()

import os, sys, time, requests
from pathlib import Path

os.environ["HF_HUB_DISABLE_SSL_VERIFICATION"] = "1"

REPO = "BAAI/bge-base-en-v1.5"
BASE_URL = f"https://huggingface.co/{REPO}/resolve/main"
SAVE_DIR = Path.home() / ".cache/huggingface/hub/models--BAAI--bge-base-en-v1.5/snapshots/main"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
(SAVE_DIR / "1_Pooling").mkdir(exist_ok=True)

FILES = [
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "sentence_bert_config.json",
    "modules.json",
    "1_Pooling/config.json",
    "model.safetensors",   # ~438 MB — main model weights
]

session = requests.Session()
session.verify = False

def download_file(filename):
    url = f"{BASE_URL}/{filename}"
    dest = SAVE_DIR / filename
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Resume support
    headers = {}
    existing = dest.stat().st_size if dest.exists() else 0
    if existing:
        headers["Range"] = f"bytes={existing}-"
        print(f"  Resuming {filename} from {existing/1024/1024:.1f} MB")
    else:
        print(f"  Downloading {filename} ...")

    try:
        r = session.get(url, headers=headers, stream=True, timeout=60)
        if r.status_code == 416:  # Already complete
            print(f"  {filename} already complete.")
            return True
        r.raise_for_status()

        total = int(r.headers.get("content-length", 0)) + existing
        mode = "ab" if existing else "wb"
        downloaded = existing

        with open(dest, mode) as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):  # 256KB chunks
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        mb = downloaded / 1024 / 1024
                        print(f"\r  {filename}: {mb:.1f}/{total/1024/1024:.1f} MB ({pct:.0f}%)", end="", flush=True)
        print(f"\n  ✓ {filename} done.")
        return True
    except Exception as e:
        print(f"\n  ✗ {filename} failed: {e}")
        return False


print("=" * 55)
print("  HIKMAH AI — Downloading BAAI/bge-base-en-v1.5")
print("=" * 55)

for f in FILES:
    for attempt in range(3):
        if download_file(f):
            break
        print(f"  Retry {attempt+1}/3 in 3s...")
        time.sleep(3)

# Write a refs file so HuggingFace hub finds the snapshot
refs_dir = Path.home() / ".cache/huggingface/hub/models--BAAI--bge-base-en-v1.5/refs"
refs_dir.mkdir(parents=True, exist_ok=True)
(refs_dir / "main").write_text("main")

print("\n" + "=" * 55)
print("  Download complete! Testing model...")
print("=" * 55)

# Test it loads
import sys
sys.path.insert(0, str(Path(__file__).parent))
from sentence_transformers import SentenceTransformer
model = SentenceTransformer(str(SAVE_DIR), device="cpu")
vec = model.encode("test", normalize_embeddings=True)
print(f"  Model works! Embedding dim: {len(vec)}")
print("  You can now run: python start_backend.py")
