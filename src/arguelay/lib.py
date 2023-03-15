import logging
import os
import pathlib
import re
import shutil

import requests

from . import log

_logger = logging.getLogger(__name__)


data_path = pathlib.Path("data")
data_path.mkdir(parents=True, exist_ok=True)


def get_var(keyname: str) -> str:
    value = os.getenv(keyname, None)
    if not os.getenv(keyname, None):
        msg = f"{keyname} not defined"
        raise ValueError(msg)

    return value


def get_url(url: str, out_path: pathlib.Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(url, stream=True)
    with open(out_path, "wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)


def get_version(path: str | pathlib.Path) -> str | None:
    re_str = r"""
    [0-9]+\.[0-9]+\.?[0-9]*
    |
    latest
    """
    versions = re.findall(re_str, str(path), re.VERBOSE | re.IGNORECASE)
    unique_versions = set(versions)
    if unique_versions:
        return list(unique_versions)[0]
    return None


def construct_url(base: str, path: str) -> str:
    x = base.rstrip("/")
    y = path.lstrip("/")
    url = f"{x}/{y}"
    return url


def download_url(url: str, path: pathlib.Path, force: bool = False):
    _logger.debug(f"fetching {url} to {path.resolve()}")
    if path.exists() and not force:
        _logger.debug(f"{path.resolve()} already exists, skipping fetch")
        return
    get_url(url, out_path=path)


def main():
    log.setup_logging()
    url_base = get_var("VAR_ARGUELAY_S3_HTTPS_URL_BASE")
    # url_parse = urllib.parse.urlparse(url_base)
    path = "/latest/win/streambox_iris_win.zip"
    url = construct_url(url_base, path)
    version = get_version(url)
    # url_parse = urllib.parse.urlparse(url)
    fname = pathlib.Path(url).name

    local_target = data_path / version / fname
    download_url(url, local_target)


if __name__ == "__main__":
    main()
