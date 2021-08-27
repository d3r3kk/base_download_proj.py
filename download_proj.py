"""download_proj.py

Starter project to download files and then do something with them.

Usage:
    download_proj.py [-j JSON] [-o OUTPUT_FOLDER] [-w WORK_FOLDER] [-V]
    download_proj.py -h | --help
    new_day.ph -v | --version


Options:
  -h --help                             Show this help and exit.
  -v --version                          Show the version of this script and exit.
  -j JSON --json-config=JSON            Input file containing the links to the
                                        downloads (if relative, will be searched
                                        for in the --work-folder).
                                        [default: download_proj.conf.json]
  -o OUTPATH --output-folder=OUTPATH    Output path to the folder containing
                                        the resulting reports. [default: .]
  -V --verbose                          Show verbose logs during processing.
  -w WORKPATH --work-folder=WORKPATH    Path to a folder where work is done,
                                        downloads saved to [default: .]
"""
import asyncio
import dataclasses
import json
import logging
import pathlib
import sys
from typing import Dict, Iterable, List

import docopt  # type: ignore
import requests
from aiohttp import ClientConnectorError, ClientSession  # type: ignore

VERSION = "0.1"

logging.basicConfig(format="[%(asctime)s]%(name)s: %(message)s", level=logging.ERROR)


@dataclasses.dataclass
class Download:
    uri: str
    local_file: pathlib.Path


@dataclasses.dataclass
class Config:
    download_groups: Dict[str, Dict[str, str]]

    def from_json(self, config_json: str) -> None:
        conf_data = json.loads(config_json)
        self.download_groups.update(conf_data["downloads"])


def download_item(uri: str, outfile: pathlib.Path) -> pathlib.Path:
    r = requests.get(uri)
    with open(outfile, "wb") as f:
        f.write(r.content)
    return outfile


def parse_config(conf_file_path: str) -> Config:
    if conf_file_path is None or conf_file_path == "":
        raise RuntimeError(
            "You must specify a configuration JSON file to continue. See --help for "
            "more information."
        )

    cnf = Config(download_groups={})
    with open(conf_file_path, "r") as f:
        cnf.from_json(config_json=f.read())

    return cnf


async def download_archives(conf: Config, output_path: pathlib.Path) -> None:
    downloads: List[Download] = []
    for download_group in conf.download_groups:
        output_path.mkdir(exist_ok=True, parents=True)
        out_folder = output_path.joinpath(download_group)
        out_folder.mkdir(exist_ok=True)
        log.debug(f"Downloading {download_group} files to {out_folder.absolute()}")

        for local_file in conf.download_groups[download_group]:
            local_file_path = out_folder.joinpath(local_file)
            dl = Download(
                uri=conf.download_groups[download_group][local_file],
                local_file=local_file_path,
            )
            downloads.append(dl)
            log.debug(f"Downloading {dl.local_file} from " f"{dl.uri}.")

    await do_multiple_downloads(downloads)


async def fetch_html(download: Download, session: ClientSession) -> tuple:
    try:
        get_response = await session.request(method="GET", url=download.uri)
        with open(download.local_file, "wb") as local_file:
            async for data in get_response.content.iter_chunked(1024):
                local_file.write(data)
    except ClientConnectorError:
        return (download.uri, 404)

    return (download.uri, get_response.status)


async def make_requests(downloads: Iterable[Download]) -> None:
    async with ClientSession() as session:
        tasks = []
        for dl in downloads:
            tasks.append(fetch_html(download=dl, session=session))
        results = await asyncio.gather(*tasks)

    for result in results:
        print(f"{result[1]} - {str(result[0])}")


async def do_multiple_downloads(downloads: Iterable[Download]):

    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."
    await make_requests(downloads=downloads)


if __name__ == "__main__":
    opts = docopt.docopt(doc=__doc__, argv=sys.argv[1:], help=True, version=VERSION)
    log_level = logging.INFO
    if opts.get("--verbose", False):
        log_level = logging.DEBUG
        log = logging.getLogger("download_proj")
        log.setLevel(log_level)
        log.debug("Setting log level to VERBOSE")

    log = logging.getLogger("download_proj")
    log.setLevel(log_level)

    log.debug("Arguments given:")
    log.debug(opts)

    work_dir = pathlib.Path(opts.get("--work-folder"))
    out_dir = pathlib.Path(opts.get("--output-folder"))
    conf_file = pathlib.Path(opts.get("--json-config"))
    if not conf_file.is_absolute():
        conf_file = work_dir.joinpath(conf_file)

    conf = parse_config(opts.get("--json-config", None))
    log.debug(
        "============================================================================="
    )
    log.debug("                        CONFIG:")
    log.debug(conf)
    log.debug(
        "============================================================================="
    )
    if sys.platform == "win32" or sys.platform == "cygwin":
        log.debug(
            "Setting asyncio library to use 'WindowsSelectorEventLoopPolicy, "
            f"as we are on a Windows machine (OS='{sys.platform}')."
        )
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(download_archives(conf=conf, output_path=out_dir))
