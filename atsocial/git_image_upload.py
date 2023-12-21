"""Code for uploading data (namely images) to the Git repository for the project."""

import os
import re
import shutil
import subprocess

import update_antarctica_today

gitrepo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class ATGit:
    """Sipmle class for handling the antarctica_today_social Git repository.

    Namely, uploading image files to the 'images' directory.
    Most actual Git development is handled externally (not using this code-base)."""

    def __init__(self):
        self.repodir = gitrepo_dir
        self.img_dir = os.path.join(self.repodir, "images")
        self.is_local_current = False

    def pull(self):
        print("> git pull")
        subprocess.run(["git", "pull"], cwd=self.repodir)
        self.is_local_current = True

    def upload_images(self, atimages_obj: update_antarctica_today.AntarcticaTodayImages):
        # First, make sure our present repo is synced with the main branch.
        if not self.is_local_current:
            self.pull()

        # The text file containing the "most recent date" updated in the repository.
        date_txtfile = os.path.join(self.img_dir, "most_recent_date.txt")
        assert os.path.exists(date_txtfile)
        repo_date_str = open(date_txtfile, 'r').read().strip()
        # Check to make sure the format of the date string is correct.
        assert re.search(r"\A\d{4}\.\d{2}\.\d{2}\Z", repo_date_str) is not None

        # Now, see whether the date in the AntarcticaTodayImages directory is the same or not.
        atimages_datestr = os.path.split(atimages_obj.dirname)[-1]
        # Make sure that's the right date format too.
        assert re.search(r"\A\d{4}\.\d{2}\.\d{2}\Z", atimages_datestr) is not None

        # If the repo has an equal-or-later date than what we have here, then do nothing.
        # Since they're both confirmed to be in a 'YYYY.MM.DD' format, a sipmle string compare will do.
        if repo_date_str >= atimages_datestr:
            print(f"Date '{repo_date_str} in Git Repo does not need to be updated with local date '{atimages_datestr}")
            return

        # If the date in the repo is outdated, then we can update the text file and images.
        repo_image_daily = os.path.join(self.img_dir, "R0_most_recent_daily.png")
        repo_image_sum = os.path.join(self.img_dir, "R0_most_recent_sum.png")
        repo_image_anomaly = os.path.join(self.img_dir, "R0_most_recent_anomaly.png")
        repo_image_line_plot = os.path.join(self.img_dir, "R0_most_recent_line_plot.png")

        # Quick sanity check to make sure the incoming images exist on disk. (Before we go deleting anything.)
        assert os.path.exists(atimages_obj.daily_melt_map)
        assert os.path.exists(atimages_obj.sum_map)
        assert os.path.exists(atimages_obj.anomaly_map)
        assert os.path.exists(atimages_obj.line_plot)

        print("Copying images and datestr to /images/ dir.")
        # First, overwrite the text file.
        open(date_txtfile, 'w').write(atimages_datestr)

        # Replace the repo images with the updated verseions.
        for new_img, repo_img in [(atimages_obj.daily_melt_map, repo_image_daily),
                                  (atimages_obj.sum_map, repo_image_sum),
                                  (atimages_obj.anomaly_map, repo_image_anomaly),
                                  (atimages_obj.line_plot, repo_image_line_plot)]:
            # Remove the old iamge.
            os.remove(repo_img)
            # Copy over the new image
            shutil.copyfile(new_img, repo_img)

        # Now, check in all the new files with Git.
        # Five add calls, one commit, one push.
        git_args = [["git", "add", "images/most_recent_date.txt"],
                    ["git", "add", "images/R0_most_recent_daily.png"],
                    ["git", "add", "images/R0_most_recent_sum.png"],
                    ["git", "add", "images/R0_most_recent_anomaly.png"],
                    ["git", "add", "images/R0_most_recent_line_plot.png"],
                    ["git", "commit", "-m",
                     "'Uploading most recent images and datestr for {0}.'".format(atimages_datestr)],
                    ["git", "push"]
                    ]

        # Run through and execute each command.
        for arglist in git_args:
            print(">", " ".join(arglist))
            subprocess.run(arglist, cwd=self.repodir)

        return
