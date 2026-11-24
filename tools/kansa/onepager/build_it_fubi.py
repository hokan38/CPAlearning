"""IT全般統制／情報処理統制の不備への対応（A4×2枚）を PDF 化し、GoodNotes 用アウトラインを付ける。"""
import glob, os, subprocess, sys
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "it_fubi.html")
OUT = os.path.join(HERE, "IT統制の不備への対応_2枚.pdf")


def find_chrome():
    for pat in ("/opt/pw-browsers/chromium_headless_shell-*/chrome-*/chrome-headless-shell",
                "/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    return "/opt/pw-browsers/chromium/chrome"


def main():
    tmp = OUT + ".tmp.pdf"
    subprocess.run([find_chrome(), "--headless", "--no-sandbox", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={tmp}", "file://" + SRC],
                   check=True, capture_output=True)
    doc = pymupdf.open(tmp)
    if doc.page_count != 2:
        sys.exit(f"expected 2 pages, got {doc.page_count}")
    doc.set_toc([[1, "① IT全般統制の不備への対応", 1], [1, "② 情報処理統制の不備への対応", 2]])
    doc.save(OUT, garbage=3, deflate=True)
    os.remove(tmp)
    print(OUT, doc.page_count)


if __name__ == "__main__":
    main()
