#!/bin/bash

WATCH_DIR="/var/www/paas/rebuild-report"
SCRIPT_TO_RUN="/var/www/paas-api/action-scripts/app_rebuild.sh"

while true; do
    /bin/bash -c "/usr/bin/inotifywait -e create /var/www/paas/rebuild-report | /bin/bash /var/www/paas-api/app_rebuild.sh"
done


