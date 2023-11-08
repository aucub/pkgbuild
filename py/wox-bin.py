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
        if "wox-linux-amd64-" in line:
            name = line.split("wox-linux-amd64-")[1].strip().split('"')[0].strip()
response = requests.get(
    "https://api.github.com/repos/"
    + os.environ.get("REPO")
    + "/releases/"
    + str(os.environ.get("LATEST"))
)
data = response.json()
if data["tag_name"].replace("-", "_") != "v" + pkgver:
    pkgver = data["tag_name"].split("v", 1)[1].replace("-", "_").strip()
    pkgrel = 1
    update = 0
for asset in data["assets"]:
    if "wox-linux-amd64-" in asset["name"]:
        if asset["name"].split("wox-linux-amd64-")[1].strip() != name:
            name = asset["name"].split("wox-linux-amd64-")[1].strip()
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
            if "wox-linux-amd64-" in line:
                line = (
                    "    "
                    + line.split("wox-linux-amd64-")[0].strip()
                    + "wox-linux-amd64-"
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
    print(f"{name}")
else:
    print(f"new")
