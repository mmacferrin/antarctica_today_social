"""
Module to run the Antarctica Today code and update the daily images.
Antarctica Today code is in a separate repository at NSIDC: https://github.com/nsidc/Antarctica_Today
Created by: Mike MacFerrin
"""

import datetime
import os
import re
import subprocess

# Update this line with the location of the python executable in which you run Antarctica Today.
at_python_exec = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              "..", "..", "..",
                                              "anaconda3", "envs", "at2", "bin", "python"
                                              )
                                 )

# Location of the "update_data.py" script in the Antarctica Today repository.
at_python_update_data_script = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                            "..", "..",
                                                            "Antarctica_Today", "antarctica_today",
                                                            "update_data.py"))

pythonpath_env_variable = {
    "PYTHONPATH": os.path.abspath(os.path.join(os.path.dirname(at_python_update_data_script), ".."))}

at_gathered_plots_dir = os.path.abspath(
    os.path.join(pythonpath_env_variable["PYTHONPATH"], "plots", "daily_plots_gathered"))


def run_update_data(run_only_if_before_yesterday: bool = True,
                    return_as_object=True):
    """Run the update_data.py script in Antartica Today, and return the new folder created.

    Return the name of the new folder created of daily plots, if they exist.
    If 'only_if_before_yesterday' is True, only actually run the code if the listed directory is more than one day old.
    The most recent it can potentially be is a one-day lag, so if yesterday's code was already run and figures were
    generated, no need to run it again, just return the folder.
    """

    # First, get the latest dated folder in the "daily_plots_gathered" directory.
    # It must be a sub-directory in that folder and follow the YYYY.MM.DD naming convention.
    dirnames = sorted([dn for dn in os.listdir(at_gathered_plots_dir)
                       if os.path.isdir(os.path.join(at_gathered_plots_dir, dn))
                       and re.search(r"\A\d{4}\.\d{2}\.\d{2}\Z", dn) is not None])
    last_dirname = dirnames[-1]

    # Check to see whether the latest date is yesterday's date. If so (and we've chosen the default option of
    # 'run_only_if_before_yesterday' = True, then we are already up-to-date and don't need to re-run the code. Just
    # return the directory.
    if run_only_if_before_yesterday:
        yesterday_date = datetime.datetime.today() - datetime.timedelta(days=1)
        if yesterday_date.strftime("%Y.%m.%d") == last_dirname:
            outdir = os.path.join(at_gathered_plots_dir, last_dirname)
            if return_as_object:
                return get_atimages_object_from_dirname(outdir)
            else:
                return outdir

    # Run the sub-process update_data.py, just for region 0.
    subprocess.run([at_python_exec, at_python_update_data_script, "-region", "0"],
                   cwd=os.path.dirname(at_python_update_data_script),
                   env=pythonpath_env_variable)

    # Now go get the directory names again. There should be a new one in there with a later date than the others.
    dirnames = sorted([dn for dn in os.listdir(at_gathered_plots_dir)
                       if os.path.isdir(os.path.join(at_gathered_plots_dir, dn))
                       and re.search(r"\A\d{4}\.\d{2}\.\d{2}\Z", dn) is not None])

    new_last_dirname = dirnames[-1]

    outdir = os.path.join(at_gathered_plots_dir, new_last_dirname)
    if return_as_object:
        return get_atimages_object_from_dirname(outdir)
    else:
        return outdir


def get_atimages_object_from_dirname(dirname,
                                     filetype="png"):
    """Given an output directory containing a day's worth of Antartcica Today images, return an AntarcticaTodayImages object.
    :param dirname: Directory name of the gathered antarctica_today images for that day.
    :param filetype: The extension of the image types to look for.
    """
    subfiles = [fn for fn in os.listdir(dirname) if
                (os.path.splitext(fn)[-1].lower().lstrip(".") == filetype.lower().lstrip("."))]

    date_subdir = os.path.split(dirname)[1]

    daily_melt_map = os.path.join(dirname,
                                  [fn for fn in subfiles if
                                   re.search(r"R0_" + date_subdir + r"_daily\.", fn) is not None][0])
    sum_map = os.path.join(dirname,
                           [fn for fn in subfiles if
                            re.search(r"R0_\d{4}-\d{4}_" + date_subdir + r"_sum\.", fn) is not None][0])
    anomaly_map = os.path.join(dirname,
                               [fn for fn in subfiles if
                                re.search(r"R0_\d{4}-\d{4}_" + date_subdir + r"_anomaly\.", fn) is not None][0])
    line_plot = os.path.join(dirname,
                             [fn for fn in subfiles if
                              re.search(r"R0_\d{4}-\d{4}_" + date_subdir + r"_gap_filled\.", fn) is not None][0])

    return AntarcticaTodayImages(dirname,
                                 daily_melt_map,
                                 sum_map,
                                 anomaly_map,
                                 line_plot)


class AntarcticaTodayImages:
    """A simple namespace class for returning image paths for the latest Antartica today images."""

    def __init__(self,
                 dirname,
                 daily_melt_map,
                 sum_map,
                 anomaly_map,
                 line_plot):
        self.dirname = dirname
        self.daily_melt_map = daily_melt_map
        self.sum_map = sum_map
        self.anomaly_map = anomaly_map
        self.line_plot = line_plot


if __name__ == "__main__":
    dname = run_update_data()
    print(dname)
    print(dname.__dict__)
    # print(dname)
    # print(os.listdir(dname))
