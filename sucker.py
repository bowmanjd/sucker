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


def copy_url(file_stem: str, url: str, extension: typing.Optional[str]) -> None:
    """Copy data from a url to a local file.

    Args:
        file_stem: name of file to use, without extensions
        url: Image URL
        extension: optional explicit file extension
    """
    print(f"Requesting {url}")
    response = urlopen(url)
    if not extension:
        content_type = response.info()["content-type"]
        extension = mimetypes.guess_extension(content_type)
        print(f"No extension specified; inferring {extension} from Content Type.")
    file_path = pathlib.Path(f"{OUT_DIR}/{file_stem}{extension}")
    with file_path.open("wb") as dest_file:
        for data in iter(partial(response.read, 32768), b""):
            dest_file.write(data)
            if done_event.is_set():
                return
    print(f"Downloaded {file_path}")


def download(csv_file: str) -> None:
    """Download multuple files to the given directory.

    Args:
        csv_file: name of CSV file to parse
    """
    pathlib.Path(OUT_DIR).mkdir(exist_ok=True)  # ensure the "out" directory exists

    in_path = pathlib.Path(csv_file)
    out_path = in_path.with_stem(f"importable_{in_path.stem}")

    with ThreadPoolExecutor(max_workers=8) as pool:
        with in_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as in_file, out_path.open("w", encoding="utf-8-sig", newline="") as out_file:
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

                new_row = {
                    "Id": row["Id"],
                    "Image_URL__c": f"{file_stem}{extension}",
                }
                writer.writerow(new_row)

                pool.submit(copy_url, file_stem, row["Image_URL__c"], extension)


def run() -> None:
    """Command runner."""
    if sys.argv[1:]:
        download(sys.argv[1])
    else:
        print("Usage:\n\tpython3 sucker.py CSV_FILE")


if __name__ == "__main__":
    run()
