import os
import re
import requests
import hashlib

update = 1
pkgrel = 0
with open(os.environ.get("PKGBUILD"), "r") as file:
    for line in file:
        if "pkgver=" in line:
            pkgver = line.split("=")[1].strip()
        if os.environ.get("ASSET") in line and os.environ.get("REPO") in line:
            name = (
                os.environ.get("ASSET")
                + line.split(os.environ.get("ASSET"))[1].strip().split('"')[0].strip()
            )
response = requests.get(
    "https://api.github.com/repos/"
    + os.environ.get("REPO")
    + "/releases/"
    + str(os.environ.get("LATEST"))
)
data = response.json()
if data["tag_name"].startswith("v"):
    new_pkgver = data["tag_name"].replace("-", "_")[1:]
else:
    new_pkgver = data["tag_name"].replace("-", "_")
if new_pkgver != pkgver:
    pkgver = new_pkgver
    pkgrel = 1
    update = 0
for asset in data["assets"]:
    if os.environ.get("ASSET") in asset["name"]:
        if asset["name"] != name:
            name = asset["name"]
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
            update = 0
if update == 0:
    lines = []
    with open(os.environ.get("PKGBUILD"), "r") as file:
        for line in file:
            if "pkgver=" in line:
                line = "pkgver=" + pkgver + "\n"
            if os.environ.get("ASSET") in line and os.environ.get("REPO") in line:
                line = (
                    "    "
                    + line.split(os.environ.get("ASSET"))[0].strip()
                    + name
                    + '"'
                    + "\n"
                )
            if "pkgrel=" in line:
                if pkgrel == 1:
                    line = "pkgrel=1" + "\n"
                else:
                    match = re.search(r"\d+", line)
                    number = int(match.group())
                    line = "pkgrel=" + str(number + 1) + "\n"
            lines.append(line)
    with open(os.environ.get("PKGBUILD"), "w") as file:
        for i, line in enumerate(lines):
            if "sha256" in line:
                lines[i + 1] = '    "' + sha256_hash.hexdigest() + '"' + "\n"
        file.writelines(lines)
    with open(
        os.environ.get("PKGBUILD").split("/")[0].strip() + "/version.txt", "w"
    ) as file:
        file.write(name)
else:
    with open(
        os.environ.get("PKGBUILD").split("/")[0].strip() + "/version.txt", "w"
    ) as file:
        file.write("new")
