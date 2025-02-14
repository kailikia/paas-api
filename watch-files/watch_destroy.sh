#!/bin/bash

WATCH_DIR="/var/www/paas/destroy-report"
SCRIPT_TO_RUN="/var/www/paas-api/action-scripts/app_destroy.sh"

while true; do
    /bin/bash -c "/usr/bin/inotifywait -e create /var/www/paas/destroy-report | /bin/bash /var/www/paas-api/app_destroy.sh"
done
