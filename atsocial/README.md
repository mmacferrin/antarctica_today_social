# Instructions for antartica_today_social code.
Warning: These instructions may be incomplete or out-of-date. They are more for my own reference than to be a public user-guide. Apologies if anything is left out.

Approximate steps to set up the antartica_today_social app:

1. **Fork or clone this repository.**

   This should be done through a git account that gives you "commit" and "push" permissions to your copy of the repository. antarctica_today_social's "git_image_upload.py" script updates your copy of the repository with the updated daily data (for display purposes) so this should not be skipped. Just downloading and unpacking a .zip archive of the code will break when it reaches this script.

2. **Download and set up the "[Antarctica_Today](https://github.com/nsidc/Antarctica_Today/tree/improve_data_updates_and_plot_generation)" code from the NSIDC Repository.**
   Note: that code is also currently under development, and the "lasest" code being used by this repository may be contained in a sub-branch other than "main" there (the link above points to the latest branch as of 2023 Dec 22). Contact the authors if you need guidance or help setting it up. You might.

3. **Update the Antarctica_Today data.**

   Some guidance is given in the [operation.md](https://github.com/nsidc/Antarctica_Today/blob/improve_data_updates_and_plot_generation/doc/operation.md) manual of the latest branch there, though we cannot guarantee it is 100% documented. Again, ask authors for guidance if needed. This code is still in prototyping and frequently undergoing change with several large re-vamps in the works.

   To link the antarctica_today_social app to the Antarctica_Today code, go into the "atsocial/update_antarctica_today.py" script and modify the "at_python..." variables at the top of that script to point the correct relative locations on your machine.

4. **Set up Mastodon and/or BlueSky apps.**

   Instructions for how to create an app can be found on the documentation for each platform. Needed credentials should be placed in CSVs in the credentials/ directory. The exact fields needed in each of those CSVs for Mastodon and Bluesky can be found in the class-implementation scripts "mastodon_social.py" and "atproto_social.py" in the atsocial/ directory.

   Other social-media platforms may be enabled as well by writing sub-class implementations for the AntTodayAppBaseClass class definition in "atsocial/anttoday_app_baseclass.py."  See examples in the Mastodon and BSky source examples noted above.

5. **Create initial posts on each platform.**

   These are not yet fully automated, I just create a post at the start of the melt season and get the post-ID from that initial post. That becomes the head post of the thread.

6. **Create post-history files for each platform for that season.**

   **a.** Create copies of the \_TEMPLATE.csv files in the "data" directory and remove the "\_TEMPLATE" portion of the names (keep the original templates there for future years.)

   **b.** Add the ID# of each post in the first (top-left) field of each csv. (This is trivial for Mastodon, copy-paste the ID# from the URL. For BlueSky, you need to query that post from the API to get the "UID" of that post. I'll clarify the easiest way to do this when I get around to it, but not today.)

   **c.** Then, run each sub-class script (mastodon_social.py and atproto_social.py) with the "-d" flag to provide a date string for the date of the data that was covered in the first post. (If no data was displayed and the first post was just an intro, then ignore the "-d" flag.) Provide dates in the "YYYY.MM.DD" format, that's what the script is expecting. This will populate and overwrite the .csv file with all the data from that first post.

7. **Run the "anttoday_social.py" script daily.**

   This can be done manually, or using a scheduler. Google "how to schedule tasks" on your operating system to find easy ways to kick off a python process daily at a specified time. If you run it on a scheduler, be sure to turn it off after April 30th, the last day of the austral "melt season" as defined in Antarctica_Today.

I do not claim the instructions in this README have been thoroughly vetted to be complete nor accurate. It is more for my own documentation as anyone's. I will attempt to update this README when I make any major updates to the code-base, but cannot guarantee it is always 100% accurate or up-to-date. If you have pressing questions or need (reasonable levels of) assistance, please contact Mike MacFerrin at the University of Colorado. (I'm not providing my email in a public-facing source files. You can google me easily enough though).

Unofficially signed,

- Mike MacFerrin