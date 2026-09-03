#!/usr/bin/env python3
import os
import re
import sys
import urllib.request
import urllib.parse

AUTHORS = [
    ("Tianrui Feng", "https://jerryfeng2003.github.io/"),
    ("Chenfeng Xu", "https://www.chenfengx.com/"),
    ("Zhi Li", "https://scholar.google.com/citations?user=C6kPjgwAAAAJ&hl"),
    ("Haocheng Xi", "https://haochengxi.github.io/"),
    ("Muyang Li", "https://lmxyy.me/"),
    ("Xiuyu Li", "https://xiuyuli.com/"),
    ("Shuo Yang", "https://andy-yang-1.github.io/"),
    ("Lvmin Zhang", "https://lllyasviel.github.io/lvmin_zhang/"),
    ("Kelly Peng", "https://www.linkedin.com/in/kellyzpeng/"),
    ("Song Han", "https://hanlab.mit.edu/songhan"),
    ("Kurt Keutzer", "https://people.eecs.berkeley.edu/~keutzer/"),
    ("Akio Kodaira", "https://scholar.google.com/citations?hl=ja&user=15X3cioAAAAJ"),
]

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "images", "authors")


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def find_image_url(html: str, base_url: str, name: str) -> str:
    # 1) Try og:image
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if m:
        return urllib.parse.urljoin(base_url, m.group(1))

    # 2) Try twitter:image
    m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if m:
        return urllib.parse.urljoin(base_url, m.group(1))

    # 3) Try scholar photo pattern
    m = re.search(r'citations\?view_op=view_photo[^"\']+', html)
    if m:
        return urllib.parse.urljoin("https://scholar.googleusercontent.com/", m.group(0))

    # 4) Try first <img> whose alt contains name parts
    first, last = name.split(" ", 1) if " " in name else (name, name)
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\'][^"\']*(%s|%s)[^"\']*["\']' % (re.escape(first), re.escape(last)), re.IGNORECASE)
    m = img_pattern.search(html)
    if m:
        return urllib.parse.urljoin(base_url, m.group(1))

    # 5) Fallback to first reasonably large image
    m = re.search(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png))["\']', html, re.IGNORECASE)
    if m:
        return urllib.parse.urljoin(base_url, m.group(1))

    return ""


def download(url: str, out_path: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with open(out_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"[warn] failed to download {url}: {e}")
        return False


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)
    mapping = {}
    for name, url in AUTHORS:
        print(f"Processing {name} -> {url}")
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[warn] fetch failed for {name}: {e}")
            continue

        img_url = find_image_url(html, url, name)
        if not img_url:
            print(f"[warn] no image found for {name}")
            continue

        ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1].lower()
        if ext not in (".jpg", ".jpeg", ".png"):
            ext = ".jpg"

        out_name = f"{slugify(name)}{ext}"
        out_path = os.path.join(OUT_DIR, out_name)
        if download(img_url, out_path):
            mapping[name] = f"static/images/authors/{out_name}"
            print(f"saved -> {mapping[name]}")
        else:
            print(f"[warn] download failed for {name}")

    # Write mapping file for later replacement
    mapping_path = os.path.join(OUT_DIR, "mapping.txt")
    with open(mapping_path, "w", encoding="utf-8") as f:
        for k, v in mapping.items():
            f.write(f"{k}\t{v}\n")
    print(f"Mapping written to {mapping_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


