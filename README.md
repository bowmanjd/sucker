# sucker

Bulk URL downloader

## Dependencies

This script requires Python 3 and the Rich library (for progress bars).

## Installation

Clone this repository, then `cd` into the directory.

Create a Python virtual environment and then install this package. Something like the following should work:

```console
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

If new to virtual environments, feel free to [read my article on the subject](https://dev.to/bowmanjd/python-tools-for-managing-virtual-environments-3bko).

## Usage

Obtain a (UTF-8 encoded) CSV file with the following structure (the header line is critical):

| Name  | SKU | URL                                              |
| ----- | --- | ------------------------------------------------ |
| Shoes | 123 | https://unsplash.com/photos/dwKiHoqqxk8/download |
| Radio | 124 | https://unsplash.com/photos/51H2LuKFHsI/download |

Then (after your Python virtual environment is activated, as above), run the following:

```sh
sucker my_csv_file.csv
```

All files will be downloaded to the `out` directory in the current working directory. This directory will be created automatically.

## Contributing

Feel free to open an issue if you have suggestions, questions, or glowing affirmations.

## Copyright and License

Copyright © 2021 Candoris. All documentation and code contained in these files may be freely shared in compliance with the [Apache License, Version 2.0][license] and is **provided “AS IS” without warranties or conditions of any kind**.

[license]: LICENSE
[apachelicense]: http://www.apache.org/licenses/LICENSE-2.0
