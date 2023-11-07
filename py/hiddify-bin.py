import os
import requests
import hashlib

update = 1
pkgrel = 0
with open(os.environ.get("PKGBUILD"), "r") as file:
    for line in file:
        if "pkgver=" in line:
            pkgver = line.split("=")[1].strip()
response = requests.get(
    "https://api.github.com/repos/" + os.environ.get("REPO") + "/releases/latest"
)
data = response.json()
if data["tag_name"].replace("-", "_") != "v" + pkgver:
    pkgver = data["tag_name"].replace("-", "_").split("v")[1].strip()
    pkgrel = 1
    update = 0
    for asset in data["assets"]:
        if "hiddify-linux-x64" in asset["name"]:
            response = requests.get(asset["browser_download_url"])
            with open(
                os.environ.get("PKGBUILD").split("/")[0].strip() + "/file", "wb"
            ) as file:
                file.write(response.content)
            sha256_hash = hashlib.sha256()
            with open(
                os.environ.get("PKGBUILD").split("/")[0].strip() + "/file", "rb"
            ) as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    sha256_hash.update(chunk)
if update == 0:
    lines = []
    with open(os.environ.get("PKGBUILD"), "r") as file:
        for line in file:
            if "pkgver=" in line:
                line = "pkgver=" + pkgver + "\n"
            if "pkgrel=" in line:
                if pkgrel == 1:
                    line = "pkgrel=1" + "\n"
            lines.append(line)
    with open(os.environ.get("PKGBUILD"), "w") as file:
        for i, line in enumerate(lines):
            if "sha256" in line:
                lines[i + 1] = '    "' + sha256_hash.hexdigest() + '"' + "\n"
        file.writelines(lines)
    print(f"{pkgver}")
else:
    print(f"0")
