import logging
import os
import pathlib
import re
import shutil
import zipfile

import jinja2
import pkg_resources
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


def unzip(zip_path: str | pathlib.Path, dst: str | pathlib.Path, force: bool = False):
    if not isinstance(zip_path, pathlib.Path):
        zip_path = pathlib.Path(zip_path)

    if not isinstance(dst, pathlib.Path):
        dst = pathlib.Path(dst)

    if dst.exists() and not force:
        _logger.debug(f"{dst.resolve()} already exists, skip unzipping")
        return

    _logger.debug(f"unzipping {zip_path.resolve()} to {dst.resolve()}")

    with zipfile.ZipFile(zip_path, "r") as zObject:
        zObject.extractall(path=dst)


def get_installer_path(base: pathlib.Path):
    msg = f"searching for exes starting at base folder {base.resolve()}"
    _logger.debug(msg)

    exes = list(base.glob("**/*.exe"))

    # unhappy path
    if len(exes) < 1:
        msg = f"couldn't find exe in {base.resolve()}"
        raise ValueError(msg)

    # unhappy path
    if len(exes) > 1:
        msg = (
            f"out of this list of installers, I don't know "
            "which one to use: "
            f"{exes}"
        )
        raise ValueError(msg)

    return exes[0]


def generate_install_cmd(s3_path_fragment: str):
    log.setup_logging()
    url_base = get_var("VAR_ARGUELAY_S3_HTTPS_URL_BASE")

    # url_parse = urllib.parse.urlparse(url_base)
    path = s3_path_fragment
    url = construct_url(url_base, path)
    version = get_version(url)
    # url_parse = urllib.parse.urlparse(url)

    local_zip_path = data_path / version / pathlib.Path(url).name

    download_url(url, local_zip_path)

    unzip_to_folder = data_path / local_zip_path.stem / version / local_zip_path.stem
    unzip(local_zip_path, unzip_to_folder)

    _logger.debug(f"{unzip_to_folder.resolve()=}")

    package = __name__.split(".")[0]
    templates_dir = pathlib.Path(pkg_resources.resource_filename(package, "templates"))

    loader = jinja2.FileSystemLoader(searchpath=templates_dir)
    env = jinja2.Environment(loader=loader, keep_trailing_newline=True)
    template = env.get_template("powershell_install.ps1.j2")

    installer_path = get_installer_path(unzip_to_folder)
    install_log_path = data_path / f"{installer_path.stem}_{version}_install.log"

    data = {
        "installer_path": str(installer_path.resolve()),
        "install_log_path": str(install_log_path.resolve()),
    }
    out = template.render(data=data)
    return out


def filter_path_from_version(path: str, version: str) -> list[str]:
    re_str = f"{version}"

    paths = re.findall(re_str, path, re.IGNORECASE)
    unique_paths = set(paths)

    msg = f"{re_str}, {path=}" if unique_paths else f"no match for {re_str} in {path=}"
    _logger.debug(msg)

    return list(unique_paths)


def main(args):
    paths = [
        "win/0.0.41/streambox_iris_win_0.0.41.zip",
        "win/0.0.42/streambox_iris_win_0.0.42.zip",
        "win/0.0.43/streambox_iris_win_0.0.43.zip",
        "win/0.0.44/streambox_iris_win_0.0.44.zip",
        "win/0.0.45/streambox_iris_win_0.0.45.zip",
        "win/0.0.46/streambox_iris_win_0.0.46.zip",
        "win/0.0.47/streambox_iris_win_0.0.47.zip",
        "win/0.0.48/streambox_iris_win_0.0.48.zip",
        "win/0.0.49/streambox_iris_win_0.0.49.zip",
        "win/0.0.50/streambox_iris_win_0.0.50.zip",
        "win/0.0.51/streambox_iris_win_0.0.51.zip",
        "win/0.0.52/streambox_iris_win_0.0.52.zip",
        "win/0.0.53/streambox_iris_win_0.0.53.zip",
        "win/0.0.54/streambox_iris_win_0.0.54.zip",
        "win/0.0.55/streambox_iris_win_0.0.55.zip",
        "win/0.2.0/streambox_iris_win_0.2.0.zip",
        "win/0.3.0/streambox_iris_win.zip",
        "win/0.3.0/streambox_iris_win_0.3.0.zip",
        "win/0.4.0/streambox_iris_win.zip",
        "win/0.4.0/streambox_iris_win_0.4.0.zip",
        "win/0.5.0/streambox_iris_win_0.5.0.zip",
        "win/0.5.1.1/streambox_iris_win.zip",
        "win/0.5.1.1/streambox_iris_win_0.5.1.1.zip",
        "win/0.5.1/streambox_iris_win_0.5.1.zip",
        "win/0.5.2.1/streambox_iris_win.zip",
        "win/0.5.3.1/streambox_iris_win.zip",
        "win/1.0.1.0/streambox_iris_win.zip",
        "win/1.0.1.1/streambox_iris_win.zip",
        "win/1.2.0.0/streambox_iris_win.zip",
        "win/1.3.0.0/streambox_iris_win.zip",
        "win/1.4.0.0/streambox_iris_win.zip",
        "win/1.5.0.0/streambox_iris_win.zip",
        "win/1.6.0.0/streambox_iris_win.zip",
        "win/1.7.0.0/streambox_iris_win.zip",
        "win/1.8.0.0/streambox_iris_win.zip",
        "win/1.9.0.0/streambox_iris_win.zip",
        "win/1.10.0.0/streambox_iris_win.zip",
        "win/1.11.0.0/streambox_iris_win.zip",
        "win/1.12.0.0/streambox_iris_win.zip",
        "win/1.13.0.0/streambox_iris_win.zip",
        "win/1.14.0.0/streambox_iris_win.zip",
        "win/1.15.0.0/streambox_iris_win.zip",
        "win/1.16.0.0/streambox_iris_win.zip",
        "win/1.17.0.0/streambox_iris_win.zip",
        "win/1.18.0.0/streambox_iris_win.zip",
        "win/1.19.0.0/streambox_iris_win.zip",
        "win/1.20.0.0/streambox_iris_win.zip",
        "win/1.21.0.0/streambox_iris_win.zip",
        "win/1.22.0.0/streambox_iris_win.zip",
        "win/1.23.0.0/streambox_iris_win.zip",
        "win/1.24.0.0/streambox_iris_win.zip",
        "win/1.25.0.0/streambox_iris_win.zip",
        "win/1.26.0.0/streambox_iris_win.zip",
        "win/1.27.0.0/streambox_iris_win.zip",
    ]

    paths = ["latest/win/streambox_iris_win.zip"] + paths
    all = []

    filters = ["."] if not args.filter_versions else args.filter_versions

    for version in filters:
        _logger.debug(f"{version=}")
        for path in paths:
            result = filter_path_from_version(path, version)
            if result:
                all.append(path)

    _logger.debug(all)

    for path in all:
        cmd = generate_install_cmd(path)
        print(cmd)


if __name__ == "__main__":
    main()
