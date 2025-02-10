#!/bin/bash

WATCH_DIR="/var/www/paas/rebuild-report"
SCRIPT_TO_RUN="/var/www/paas-api/action-files/app_rebuild.sh"

while true; do
    /usr/bin/inotifywait -e create "$WATCH_DIR" && /bin/bash "$SCRIPT_TO_RUN"
    sleep 1  # Prevent high CPU usage
done


