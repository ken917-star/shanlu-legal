#!/usr/bin/env python3
"""
善録 法務ページ GitHub Pages 一键推送脚本
用法: python3 push_to_github.py <YOUR_GITHUB_PAT>

需要 PAT 权限: repo (Contents: Read and write)
创建 PAT: https://github.com/settings/tokens/new

前置: 在 GitHub 创建仓库 ken917-star/shanlu-legal，并在 Settings → Pages
      启用 GitHub Pages (Branch: main / root)。
本脚本会创建或更新仓库内文件 (首次推送会自动创建)。
发布后法务 URL 形如:
  https://ken917-star.github.io/shanlu-legal/privacy-ja.html
  https://ken917-star.github.io/shanlu-legal/terms-ja.html
"""
import sys
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

REPO   = "ken917-star/shanlu-legal"
BRANCH = "main"
FILES  = [
    "index.html", "style.css",
    "privacy-ja.html", "privacy-en.html", "privacy-zh.html", "privacy-zh-TW.html",
    "terms-ja.html",   "terms-en.html",   "terms-zh.html",   "terms-zh-TW.html",
]

def api(token, method, path, data=None):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def get_sha(token, filename):
    """返回远端文件 sha，不存在则 None (用于 create-or-update)。"""
    try:
        info = api(token, "GET", f"/repos/{REPO}/contents/{filename}?ref={BRANCH}")
        return info["sha"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

def push_files(token):
    script_dir = Path(__file__).parent
    ok = 0
    for filename in FILES:
        filepath = script_dir / filename
        if not filepath.exists():
            print(f"SKIP {filename} (not found locally)")
            continue
        content = filepath.read_bytes()
        b64 = base64.b64encode(content).decode()
        sha = get_sha(token, filename)
        payload = {
            "message": f"Publish {filename}",
            "content": b64,
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha
        api(token, "PUT", f"/repos/{REPO}/contents/{filename}", payload)
        print(f"OK  {filename}{' (updated)' if sha else ' (created)'}")
        ok += 1
    print(f"\n✓ {ok}/{len(FILES)} files pushed to {REPO}")
    print("GitHub Pages 发布后约 1 分钟生效，URL 见脚本顶部说明。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    push_files(sys.argv[1].strip())
