import hashlib
import os
import re
import requests as req

# 获取环境变量
pkgbuild_path = os.environ.get("PKGBUILD")
repo = os.environ.get("REPO")
latest = os.environ.get("LATEST")

# 初始化变量
update = 1
pkg_rel = 0
pkgver = None
new_pkgver = None
tag_name = None
sha256_hash = None

# 检查 PKGBUILD 文件是否存在
if os.path.exists(pkgbuild_path):
    with open(pkgbuild_path, "r", encoding="utf-8") as file:
        for line in file:
            # 查找 pkgver
            if "pkgver=" in line:
                pkgver = re.search(r"pkgver=(.*)", line).group(1).strip()

# 发起 API 请求
response = req.get(
    f"https://api.github.com/repos/{repo}/releases/{latest}",
    headers={"User-Agent": "Mozilla/5.0"},
)

# 检查 API 响应状态码
if response.status_code == 200:
    data = response.json()
    if "tag_name" in data:
        tag_name = data["tag_name"]
        if tag_name.startswith("v"):
            new_pkgver = tag_name.replace("-", "_")[1:]
        else:
            new_pkgver = tag_name.replace("-", "_")
        if new_pkgver != pkgver:
            pkgver = new_pkgver
            pkg_rel = 1
            update = 0
            response = req.get(
                data["zipball_url"], headers={"User-Agent": "Mozilla/5.0"}
            )
            if response.status_code == 200:
                file_path = os.path.join(os.path.dirname(pkgbuild_path), "file")
                with open(file_path, "wb") as file:
                    file.write(response.content)
                    sha256_hash = hashlib.sha256()
                    with open(file_path, "rb") as file:
                        for chunk in iter(lambda: file.read(4096), b""):
                            sha256_hash.update(chunk)

# 更新 PKGBUILD 文件
if update == 0:
    lines = []
    with open(pkgbuild_path, "r", encoding="utf-8") as file:
        for line in file:
            if "pkgver=" in line:
                line = f"pkgver={pkgver}\n"
            if "pkgrel=" in line:
                if pkg_rel == 1:
                    line = "pkgrel=1\n"
            lines.append(line)
    with open(pkgbuild_path, "w", encoding="utf-8") as file:
        for line, next_line in zip(lines, lines[1:] + [""]):
            if "sha256" in line:
                next_line = f'    "{sha256_hash.hexdigest()}"\n'
            file.write(line)
            file.write(next_line)
    name = data["tag_name"]
    version_file_path = os.path.join(os.path.dirname(pkgbuild_path), "version.txt")
    with open(version_file_path, "w", encoding="utf-8") as file:
        file.write(name)
else:
    version_file_path = os.path.join(os.path.dirname(pkgbuild_path), "version.txt")
    with open(version_file_path, "w", encoding="utf-8") as file:
        file.write("new")
