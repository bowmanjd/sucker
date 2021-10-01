"""A bulk URL downloader with progress bars."""

import csv
import mimetypes
import pathlib
import re
import signal
import sys
import typing
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Event
from urllib.parse import urlparse
from urllib.request import urlopen

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
    auto_refresh=False,
)

unwanted_characters = re.compile("[^A-Za-z0-9_-]+")


OUT_DIR = "out"

done_event = Event()


def signal_handler(signal_number, frame):  # type: ignore
    """Handle signals.

    Args:
        signal_number: signal code
        frame: signal frame
    """
    done_event.set()


signal.signal(signal.SIGINT, signal_handler)


def copy_url(
    task_id: TaskID, file_stem: str, url: str, extension: typing.Optional[str]
) -> None:
    """Copy data from a url to a local file.

    Args:
        task_id: task id for progress bar
        file_stem: name of file to use, without extensions
        url: Image URL
        extension: optional explicit file extension
    """
    progress.console.log(f"Requesting {url}")
    response = urlopen(url)
    if not extension:
        content_type = response.info()["content-type"]
        extension = mimetypes.guess_extension(content_type)
        progress.console.log(
            f"No extension specified; inferring {extension} from Content Type."
        )
    file_path = pathlib.Path(f"{OUT_DIR}/{file_stem}{extension}")
    progress.update(task_id, total=int(response.info()["Content-length"]))
    with file_path.open("wb") as dest_file:
        progress.start_task(task_id)
        for data in iter(partial(response.read, 32768), b""):
            dest_file.write(data)
            progress.update(task_id, advance=len(data), visible=True, refresh=True)
            if done_event.is_set():
                return
    progress.console.log(f"Downloaded {file_path}")


def download(csv_file: str) -> None:
    """Download multuple files to the given directory.

    Args:
        csv_file: name of CSV file to parse
    """
    pathlib.Path(OUT_DIR).mkdir(exist_ok=True)  # ensure the "out" directory exists

    in_path = pathlib.Path(csv_file)
    out_path = in_path.with_stem(f"importable_{in_path.stem}")

    with progress:
        with ThreadPoolExecutor(max_workers=8) as pool:
            with in_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as in_file, out_path.open(
                "w", encoding="utf-8-sig", newline=""
            ) as out_file:
                reader = csv.DictReader(in_file)
                writer = csv.DictWriter(out_file, ["Id", "Image_URL__c"])
                writer.writeheader()
                for row in reader:
                    file_stem = "_".join(row["Name"].split()).lower()
                    file_stem = unwanted_characters.sub("", file_stem)
                    file_stem = "-".join([file_stem, row["StockKeepingUnit"].strip()])
                    original_path = pathlib.PurePosixPath(
                        urlparse(row["Image_URL__c"]).path
                    )
                    extension = original_path.suffix
                    task_id = progress.add_task(
                        "download", filename=file_stem, start=False, visible=True
                    )

                    new_row = {
                        "Id": row["Id"],
                        "Image_URL__c": f"{file_stem}{extension}",
                    }
                    writer.writerow(new_row)

                    pool.submit(
                        copy_url, task_id, file_stem, row["Image_URL__c"], extension
                    )


def run() -> None:
    """Command runner."""
    if sys.argv[1:]:
        download(sys.argv[1])
    else:
        print("Usage:\n\tpython3 sucker.py CSV_FILE")


if __name__ == "__main__":
    run()
