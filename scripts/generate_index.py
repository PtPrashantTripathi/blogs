import os
import subprocess
from datetime import datetime

ROOT = os.getcwd()
OUTPUT_FILE = os.path.join(ROOT, "index.html")


def find_html_files():
    html_files = []
    for root, dirs, files in os.walk(ROOT):
        if ".git" in root:
            continue
        for file in files:
            if file.endswith(".html") and file != "index.html":
                html_files.append(os.path.join(root, file))
    return html_files


def get_creation_date(filepath):
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


posts = []

for file in find_html_files():
    rel_path = os.path.relpath(file, ROOT).replace("\\", "/")
    title = (
        os.path.splitext(os.path.basename(file))[0]
        .replace("-", " ")
        .replace("_", " ")
        .title()
    )

    created_at = get_creation_date(file)
    posts.append(
        {
            "title": title,
            "path": rel_path,
            "date": created_at,
        }
    )

# Sort newest first
posts.sort(key=lambda x: x["date"] or datetime.min, reverse=True)

# Generate HTML
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>My Blog</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-800">
  <div class="max-w-4xl mx-auto py-10 px-4">
    <h1 class="text-4xl font-bold mb-6">📚 Blog</h1>

    <div class="space-y-4">
"""

for post in posts:
    date_str = post["date"].strftime("%d %b %Y") if post["date"] else "Unknown"
    html += f"""
      <a href="{post['path']}"
         class="block p-5 bg-white rounded-xl shadow hover:shadow-md transition">
        <h2 class="text-2xl font-semibold">{post['title']}</h2>
        <p class="text-sm text-gray-500 mt-1">Posted on {date_str}</p>
      </a>
"""

html += """
    </div>
  </div>
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print("index.html generated successfully.")
