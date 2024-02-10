import hashlib
import os
import requests

# 获取环境变量
pkgbuild_path = os.environ.get("PKGBUILD")
repo_name = os.environ.get("REPO")
latest_version = os.environ.get("LATEST")

# 初始化变量
update = 1
pkgrel = 0
pkgver = None
new_pkgver = None
tag_name = None
sha256_hash = None

# 检查 PKGBUILD 文件
if os.path.exists(pkgbuild_path):
    with open(pkgbuild_path, "r", encoding="utf-8") as file:
        for line in file:
            # 查找 pkgver
            if "pkgver=" in line:
                pkgver = line.split("=")[1].strip()

# 发起 API 请求
response = requests.get(
    "https://api.github.com/repos/" + repo_name + "/releases/" + str(latest_version)
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
        if new_pkgver not in pkgver:
            pkgver = new_pkgver
            pkgrel = 1
            update = 0
            response = requests.get(data["zipball_url"])
            if response.status_code == 200:
                content = response.content
                sha256_hash = hashlib.sha256()
                sha256_hash.update(content)
                digest = sha256_hash.hexdigest()

# 更新 PKGBUILD 文件
if update == 0:
    lines = []
    with open(pkgbuild_path, "r", encoding="utf-8") as file:
        for line in file:
            if "pkgver=" in line:
                line = "pkgver=" + pkgver + "\n"
            if "pkgrel=" in line:
                if pkgrel == 1:
                    line = "pkgrel=1" + "\n"
            lines.append(line)
    with open(pkgbuild_path, "w") as file:
        for i, line in enumerate(lines):
            if "sha256" in line:
                lines[i + 1] = '    "' + digest + '"' + "\n"
                break
        file.writelines(lines)
    name = data["tag_name"]
    version_file_path = os.path.join(os.path.dirname(pkgbuild_path), "version.txt")
    with open(version_file_path, "w", encoding="utf-8") as file:
        file.write(name)
else:
    version_file_path = os.path.join(os.path.dirname(pkgbuild_path), "version.txt")
    with open(version_file_path, "w", encoding="utf-8") as file:
        file.write("new")
