# download_data.py - Kristian Kesar, C00296348
#
# downloads the apachejit csvs into data/raw/
# run it from the main project folder:  python scripts/download_data.py

import urllib.request
from pathlib import Path

# locked to one exact version of their repo so the data never changes on me
COMMIT = "ddfd547ff8e3d3725f6a1fd0f177c0ebe085a4b5"
URL = f"https://raw.githubusercontent.com/hosseinkshvrz/apachejit/{COMMIT}/dataset"

FILES = [
    "apachejit_total.csv",       # everything, ~106k commits
    "apachejit_train.csv",       # 2003-2016, for training
    "apachejit_test_large.csv",  # 2017-2019, for testing
    "apachejit_test_small.csv",  # smaller test set for quick checks
]

folder = Path("data/raw")
folder.mkdir(parents=True, exist_ok=True)

for name in FILES:
    target = folder / name
    if target.exists():
        print(f"already got {name}, skipping")
        continue
    print(f"downloading {name}...")
    urllib.request.urlretrieve(f"{URL}/{name}", target)

print("done")
