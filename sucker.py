"""A bulk URL downloader with progress bars."""

import csv
import mimetypes
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from threading import Event
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
)


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


def copy_url(task_id: TaskID, name: str, sku: str, url: str) -> None:
    """Copy data from a url to a local file.

    Args:
        task_id: task id for progress bar
        name: Product name
        sku: Product sku
        url: Image URL
    """
    progress.console.log(f"Requesting {url}")
    response = urlopen(url)
    content_type = response.info()["content-type"]
    extension = mimetypes.guess_extension(content_type)
    file_path = Path(
        f"{OUT_DIR}/{'_'.join(name.split()).lower()}-{sku.strip()}{extension}"
    )
    progress.update(task_id, total=int(response.info()["Content-length"]))
    with file_path.open("wb") as dest_file:
        progress.start_task(task_id)
        for data in iter(partial(response.read, 32768), b""):
            dest_file.write(data)
            progress.update(task_id, advance=len(data), visible=True)
            if done_event.is_set():
                return
    progress.console.log(f"Downloaded {file_path}")


def download(csv_file: str) -> None:
    """Download multuple files to the given directory.

    Args:
        csv_file: name of CSV file to parse
    """
    Path(OUT_DIR).mkdir(exist_ok=True)  # ensure the "out" directory exists

    in_path = Path(csv_file)

    with progress:
        with ThreadPoolExecutor(max_workers=8) as pool:
            with in_path.open("r", newline="", encoding="utf-8-sig") as in_file:
                reader = csv.DictReader(in_file)
                for row in reader:
                    task_id = progress.add_task(
                        "download", filename=row["Name"], start=False, visible=False
                    )
                    pool.submit(copy_url, task_id, row["Name"], row["SKU"], row["URL"])


def run() -> None:
    """Command runner."""
    if sys.argv[1:]:
        download(sys.argv[1])
    else:
        print("Usage:\n\tpython3 sucker.py CSV_FILE")


if __name__ == "__main__":
    run()
