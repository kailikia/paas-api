#!/bin/bash

WATCH_DIR="/var/www/paas/success-report"
SCRIPT_TO_RUN="/var/www/paas-api/action-scripts/app_deployment.sh"


while true; do
    /bin/bash -c "/usr/bin/inotifywait -e create /var/www/paas/success-report | /bin/bash /var/www/paas-api/app_deployment.sh"
done


