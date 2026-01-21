import os
import subprocess
from datetime import datetime
import xml.dom.minidom as minidom
from xml.etree.ElementTree import Element, SubElement, ElementTree

ROOT = os.getcwd()
BASE_URL = "https://ptprashanttripathi.github.io/blogs/"
GA_ID = "G-C4NJD8J3MD"

INDEX_FILE = os.path.join(ROOT, "index.html")
SITEMAP_FILE = os.path.join(ROOT, "sitemap.xml")

GA_SNIPPET = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_ID}');
</script>
"""


def find_html_files():
    html_files = []
    for root, _, files in os.walk(ROOT):
        if ".git" in root:
            continue
        for f in files:
            if f.endswith(".html") and f != "index.html":
                html_files.append(os.path.join(root, f))
    return html_files


def git_created_date(filepath):
    try:
        result = subprocess.check_output(
            [
                "git",
                "log",
                "--diff-filter=A",
                "--follow",
                "--format=%aI",
                "--",
                filepath,
            ],
            stderr=subprocess.DEVNULL,
        ).decode().strip().split("\n")[-1]

        return datetime.fromisoformat(result.replace("Z", "+00:00"))
    except Exception:
        return None


def inject_ga_if_missing(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if GA_ID in content:
        return False

    if "</head>" not in content:
        return False

    content = content.replace("</head>",  GA_SNIPPET + "\n</head>", 1)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return True


posts = []
ga_injected = []

for file in find_html_files():
    rel_path = os.path.relpath(file, ROOT).replace("\\", "/")

    if inject_ga_if_missing(file):
        ga_injected.append(rel_path)

    title = (
        os.path.splitext(os.path.basename(file))[0]
        .replace("-", " ")
        .replace("_", " ")
        .title()
    )

    posts.append(
        {
            "title": title,
            "path": rel_path,
            "date": git_created_date(file),
        }
    )

posts.sort(key=lambda x: x["date"] or datetime.min, reverse=True)

# -------------------------
# Generate index.html
# -------------------------
html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Blogs</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
  <main class="max-w-4xl mx-auto p-6">
    <h1 class="text-4xl font-bold mb-6">📚 Blogs</h1>
    <div class="space-y-4">
"""

for post in posts:
    date_str = post["date"].strftime("%d %b %Y") if post["date"] else "Unknown"
    html += f"""
      <a href="{post['path']}" class="block bg-white p-5 rounded-xl shadow hover:shadow-lg transition">
        <h2 class="text-2xl font-semibold">{post['title']}</h2>
        <p class="text-gray-500 text-sm mt-1">Posted on {date_str}</p>
      </a>"""

html += """
    </div>
  </main>
</body>
</html>
"""

with open(INDEX_FILE, "w", encoding="utf-8") as f:
    f.write(html)

# -------------------------
# Generate sitemap.xml
# -------------------------
urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

for post in posts:
    url = SubElement(urlset, "url")
    SubElement(url, "loc").text = BASE_URL + post["path"]
    if post["date"]:
        SubElement(url, "lastmod").text = post["date"].strftime("%Y-%m-%d")

# ElementTree(urlset).write(SITEMAP_FILE, encoding="utf-8", xml_declaration=True)
rough_tree = ElementTree(urlset)
rough_string = minidom.parseString(
    ElementTree.tostring(urlset, encoding="utf-8", xml_declaration=True)
)

pretty_xml = rough_string.toprettyxml(indent="\t", encoding="utf-8")

with open(SITEMAP_FILE, "wb") as f:
    f.write(pretty_xml)


# -------------------------
# Log GA injections
# -------------------------
if ga_injected:
    print("\n✅ Google Tag injected into:")
    for f in ga_injected:
        print(f" - {f}")
else:
    print("\n✅ Google Tag already present in all files")

print("\n✅ index.html & sitemap.xml generated")
