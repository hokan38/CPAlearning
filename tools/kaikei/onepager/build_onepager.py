"""1枚もの HTML を A4 PDF にする。使い方: python3 build_onepager.py <html> <pdf> <outline title>"""
import glob, os, subprocess, sys
import pymupdf


def find_chrome():
    for pat in ("/opt/pw-browsers/chromium_headless_shell-*/chrome-*/chrome-headless-shell",
                "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return "/opt/pw-browsers/chromium/chrome"


def main(src, out, title):
    src, out = os.path.abspath(src), os.path.abspath(out)
    tmp = out + ".tmp.pdf"
    subprocess.run([find_chrome(), "--headless", "--no-sandbox", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={tmp}", "file://" + src],
                   check=True, capture_output=True)
    doc = pymupdf.open(tmp)
    doc.set_toc([[1, title, 1]])
    doc.save(out, garbage=3, deflate=True)
    os.remove(tmp)
    print(out, doc.page_count)


if __name__ == "__main__":
    main(*sys.argv[1:4])
