import os
import re
import requests
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS_FILE = os.path.join(BASE_DIR, "external-links.txt")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded-assets")

def setup():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    css_dir = os.path.join(DOWNLOAD_DIR, "css")
    js_dir = os.path.join(DOWNLOAD_DIR, "js")
    fonts_dir = os.path.join(DOWNLOAD_DIR, "fonts")
    fonts2_dir = os.path.join(DOWNLOAD_DIR, "fonts2")
    for d in [css_dir, js_dir, fonts_dir, fonts2_dir]:
        os.makedirs(d, exist_ok=True)
    return css_dir, js_dir, fonts_dir, fonts2_dir

def get_save_path(url, css_dir, js_dir, fonts_dir, fonts2_dir):
    parsed = urlparse(url)
    path = parsed.path
    filename = os.path.basename(path)
    if not filename:
        filename = "index.html"

    if "/fonts/" in path or "/google-fonts/" in path or "fonts.googleapis" in url or "fonts.gstatic" in url:
        return os.path.join(fonts_dir, filename), "fonts"
    elif "font-awesome" in path or "useanyfont" in path:
        return os.path.join(fonts2_dir, filename), "fonts2"
    elif path.endswith(".css") or path.endswith(".css?") or "/css/" in path:
        return os.path.join(css_dir, filename), "css"
    elif path.endswith(".js") or "/js/" in path or path.endswith(".js?"):
        return os.path.join(js_dir, filename), "js"
    else:
        return os.path.join(css_dir, filename), "other"

def clean_filename(url):
    parsed = urlparse(url)
    path = parsed.path
    query = parsed.query
    filename = os.path.basename(path)
    if not filename or filename == "/":
        filename = path.replace("/", "_").strip("_") + ".html"
    if query:
        filename = filename.replace("?" + query, "")
    return filename

def download_all():
    css_dir, js_dir, fonts_dir, fonts2_dir = setup()

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    links = []
    current_section = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("=") or line.startswith("TOTAL"):
            continue
        if line.startswith("["):
            current_section = line
            continue
        if line.startswith("http"):
            links.append((line, current_section))

    print(f"[INFO] Found {len(links)} external links to download.")
    print(f"[INFO] Download directory: {DOWNLOAD_DIR}")
    print("=" * 60)

    success = 0
    failed = 0
    skipped = 0

    for url, section in links:
        try:
            parsed = urlparse(url)
            filename = clean_filename(url)
            filepath, folder = get_save_path(url, css_dir, js_dir, fonts_dir, fonts2_dir)

            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                print(f"[SKIP] {filename} (already exists)")
                skipped += 1
                continue

            print(f"[DL] {url}")
            response = requests.get(url, timeout=30, allow_redirects=True)

            if response.status_code == 200:
                with open(filepath, "wb") as out_file:
                    out_file.write(response.content)
                size_kb = len(response.content) / 1024
                print(f"  -> Saved to: {filepath} ({size_kb:.1f} KB)")
                success += 1
            else:
                print(f"  -> FAILED: HTTP {response.status_code}")
                failed += 1

        except requests.exceptions.Timeout:
            print(f"  -> TIMEOUT: {url}")
            failed += 1
        except requests.exceptions.ConnectionError:
            print(f"  -> CONNECTION ERROR: {url}")
            failed += 1
        except Exception as e:
            print(f"  -> ERROR: {e}")
            failed += 1

    print("=" * 60)
    print(f"[DONE] Success: {success} | Failed: {failed} | Skipped: {skipped}")
    print(f"[DONE] All files saved to: {DOWNLOAD_DIR}")

    summary_file = os.path.join(DOWNLOAD_DIR, "download_summary.txt")
    with open(summary_file, "w", encoding="utf-8") as sf:
        sf.write("DOWNLOAD SUMMARY\n")
        sf.write("=" * 60 + "\n")
        sf.write(f"Total links: {len(links)}\n")
        sf.write(f"Success: {success}\n")
        sf.write(f"Failed: {failed}\n")
        sf.write(f"Skipped: {skipped}\n")
        sf.write("=" * 60 + "\n\n")
        sf.write("FAILED LINKS:\n")
        for url, section in links:
            filename = clean_filename(url)
            filepath, folder = get_save_path(url, css_dir, js_dir, fonts_dir, fonts2_dir)
            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                sf.write(f"  {url} -> {filepath}\n")

    print(f"[INFO] Summary saved to: {summary_file}")

if __name__ == "__main__":
    download_all()
