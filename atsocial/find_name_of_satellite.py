"""Code for detecting which satellite a given daily Antarctica Today melt data came from."""
from pathlib import Path

antarctica_today_dir = Path(__file__).absolute().parent.parent.parent / "Antarctica_Today"
print(str(antarctica_today_dir))


def expanded_name(short_name: str) -> str:
    pass
    # Turn "F18" into "DMSP-F18", and similar.


def return_satellite_name(datestr: str, expanded_name: bool = True) -> str:
    pass
    # TODO: Go into the Antarctica_Today/Tb/nsidc-0080 directory, find the Tb file corresponding with this datestr.
    # TODO: Then, read the /constants/satellites.py file, and get the first satellite in that list which is
    # TODO: included in that file. This is the way Antarctica_Today does it, it *should* work for now until we get the
    # TODO: satellite name encoded along with the data. But this is a hold-over function for now.
