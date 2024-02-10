import os
import re
import requests
import hashlib

update = 1
pkgrel = 0

# 获取环境变量
pkgbuild_path = os.environ.get("PKGBUILD")
asset_name = os.environ.get("ASSET")
repo_name = os.environ.get("REPO")
latest_version = os.environ.get("LATEST")

# 检查 PKGBUILD 文件是否存在
if not os.path.exists(pkgbuild_path):
    raise FileNotFoundError("PKGBUILD file not found")

# 读取 PKGBUILD 文件
with open(pkgbuild_path, "r") as file:
    for line in file:
        if "pkgver=" in line:
            pkgver = line.split("=")[1].strip()
        if asset_name in line and repo_name in line:
            name = asset_name + line.split(asset_name)[1].strip().split('"')[0].strip()
            break

# 发送请求获取 GitHub API 数据
response = requests.get(
    "https://api.github.com/repos/" + repo_name + "/releases/" + str(latest_version),
    timeout=10,
)

# 检查响应状态码
if response.status_code != 200:
    raise ValueError("Invalid response from GitHub API")

# 解析响应数据
try:
    data = response.json()
except ValueError:
    raise ValueError("Invalid JSON response from GitHub API")

# 检查版本号是否以 "v" 开头
if data["tag_name"].startswith("v"):
    new_pkgver = data["tag_name"].replace("-", "_")[1:]
else:
    new_pkgver = data["tag_name"].replace("-", "_")

# 更新版本号和 pkgver
if new_pkgver not in pkgver:
    pkgver = new_pkgver
    version = pkgver
    pkgrel = 1
    update = 0

# 下载并验证文件
for asset in data["assets"]:
    if asset_name in asset["name"]:
        if asset["name"] not in name:
            name = asset["name"]
            version = name
            update = 0
        try:
            response = requests.get(asset["browser_download_url"], timeout=60)
        except requests.exceptions.RequestException:
            raise ValueError("Failed to download file")
        content = response.content
        sha256_hash = hashlib.sha256()
        sha256_hash.update(content)
        digest = sha256_hash.hexdigest()

# 更新 PKGBUILD 文件和版本号文件
if update == 0:
    lines = []
    with open(pkgbuild_path, "r") as file:
        for line in file:
            if "pkgver=" in line:
                line = "pkgver=" + pkgver + "\n"
            if asset_name in line and repo_name in line:
                line = "    " + line.split(asset_name)[0].strip() + name + '"' + "\n"
            if "pkgrel=" in line:
                if pkgrel == 1:
                    line = "pkgrel=1" + "\n"
                else:
                    match = re.search(r"\d+", line)
                    number = int(match.group())
                    line = "pkgrel=" + str(number + 1) + "\n"
            lines.append(line)
    with open(pkgbuild_path, "w") as file:
        for i, line in enumerate(lines):
            if "sha256" in line:
                lines[i + 1] = '    "' + digest + '"' + "\n"
                break
        file.writelines(lines)
    with open(os.path.join(os.path.dirname(pkgbuild_path), "version.txt"), "w") as file:
        file.write(version)
else:
    with open(os.path.join(os.path.dirname(pkgbuild_path), "version.txt"), "w") as file:
        file.write("new")
