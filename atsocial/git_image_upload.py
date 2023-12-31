"""Code for uploading data (namely images) to the Git repository for the project."""

import os
import re
import shutil
import subprocess

import add_date_to_readme
import update_antarctica_today

# This should point to the base directory of this repo. In this case, one parent directory up.
gitrepo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class ATGit:
    """Sipmle class for handling the antarctica_today_social Git repository.

    Namely, uploading image files to the 'images' directory.
    Most actual Git development is handled externally (not using this code-base)."""

    def __init__(self):
        self.repodir = gitrepo_dir
        self.img_dir = os.path.join(self.repodir, "images")
        self.is_local_current = False
        self.git_cmd = "/usr/bin/git"

    def pull(self):
        print("> git pull")
        subprocess.run([self.git_cmd, "pull"], cwd=self.repodir)
        self.is_local_current = True

    def upload_images(self,
                      atimages_obj: update_antarctica_today.AntarcticaTodayImages,
                      also_update_readme: bool = True):
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
            print(f"Date {repo_date_str} in Git Repo does not need to be updated with local date {atimages_datestr}")
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

        was_readme_changed = False
        if also_update_readme:
            was_readme_changed = add_date_to_readme.substitute_date_in_readme()

        # Now, check in all the new files with Git.
        # Start with a pull command to bring the local repo up-to-date, avoiding blocking conflicts.
        # Then five or six add calls to add the new files, one commit, and one push up to the repository.
        # Note: ":" is the bash "do nothing" command, which we use if the readme wasn't updated at all.
        git_cmd = self.git_cmd
        git_args = [[git_cmd, "add", "images/most_recent_date.txt"],
                    [git_cmd, "add", "images/R0_most_recent_daily.png"],
                    [git_cmd, "add", "images/R0_most_recent_sum.png"],
                    [git_cmd, "add", "images/R0_most_recent_anomaly.png"],
                    [git_cmd, "add", "images/R0_most_recent_line_plot.png"],
                    [git_cmd, "add", "README.md"] if was_readme_changed else [':'],
                    [git_cmd, "commit", "-m", "Uploading most recent images for {0}.".format(atimages_datestr)],
                    [git_cmd, "push"]
                    ]

        # Run through and execute each command.
        for arglist in git_args:
            print(">", " ".join(arglist))
            subprocess.run(arglist, cwd=self.repodir)

        return


if __name__ == "__main__":
    # Running this module standalone just takes the data as-is in the local repo and tries to update the Git with it.
    # Useful if (for some reason) the git didn't update.
    at_update_object = update_antarctica_today.run_update_data(skip_update_and_just_get_object=True)

    # Upload the new images to the git repository. (This will exit out if the git is alredy current.)
    atgit = ATGit()
    atgit.upload_images(at_update_object, also_update_readme=True)
