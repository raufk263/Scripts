#!/bin/bash

# Directory where screenshots are stored, Modify it according to your file location.
screenshot_dir="/home/rauf/Pictures/Screenshots/"

# Delete screenshots older than 7 days
find "$screenshot_dir" -type f -name "*.png" -mtime +7 -exec rm {} \;

#-----------------------------------------------------------------
# To Move the screenshots to trash instead of rm add below line--


# find "$screenshot_dir" -type f -name "*.png" -mtime +7 -exec gio trash {} \;

#---------------------------------------------------------------------------------------------------------README----------------------------------------------------------------------------------------------
#This is bash script created to delete an screesnhot older than 7 days. It's an demonstration of script that is used in screesnshot case but the scenario can be deleting log files older than 7 days
#or X no. of days from the server.

#Step 1 - Create an bash script named DeleteSS.sh

#Step 2 - Schedule an cron Job which will be executed every 7 day to execute the script.

#For creating cron Job to be executed every 7 day.

# Enter command on termianl crontab -e and paste the 2nd line in crontab

# $ crontab -e
# 0 0 * * */7  /home/rauf/BashScripts/DeleteSS.h

#-----------------------------------------------------------------------------------------------THANK YOU !!---------------------------------------------------------------------------------------------------
