import shutil
import stat
import requests
import tqdm
import os,pathlib
import tarfile
import tempfile
import warnings
import zipfile
from base64 import b64encode
from io import BytesIO
from pathlib import Path

ulrs = "https://solc-bin.ethereum.org/windows-amd64/list.json"

resulst = requests.get(ulrs).json()


def _download_solc(url: str) -> bytes:
    print(f"Downloading from {url}")
    response = requests.get(url)
    if response.status_code == 404:
        print(
            "404 error when attempting to download from {} - are you sure this"
            " version of solidity is available?".format(url)
        )
    if response.status_code != 200:
        raise print(
            f"Received status code {response.status_code} when attempting to download from {url}"
        )

    return response.content


def _get_temp_folder() -> Path:
    path = Path(tempfile.gettempdir()).joinpath(f"solcx-tmp-{os.getpid()}")
    if path.exists():
        shutil.rmtree(str(path))
    path.mkdir()
    return path


BINARY_DOWNLOAD_BASE = "https://solc-bin.ethereum.org/windows-amd64/{}"

for key in resulst['releases'].keys():
    filename = resulst['releases'][key]

    print(f"key: {key}, filename: {filename}")

    download = BINARY_DOWNLOAD_BASE.format(filename)
    # install_path = Path(r"C:\Users\Chao Ni\.solcx").joinpath(f"solc-v{key}")
    install_path = Path(r"C:\Users\yuanruifan\Desktop\TEST\.solcx").joinpath(f"solc-v{key}")


    temp_path = _get_temp_folder()
    content = _download_solc(download)
    with zipfile.ZipFile(BytesIO(content)) as zf:
        zf.extractall(str(temp_path))

    temp_path.rename(install_path)




