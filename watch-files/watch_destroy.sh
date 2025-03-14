#!/bin/bash

WATCH_DIR="/var/www/paas/destroy-report"
SCRIPT_TO_RUN="/var/www/paas-api/action-scripts/app_destroy.sh"
LOG_FILE="/var/log/supervisor/paas_supervisor_stdout.log"


echo "$(date '+%Y-%m-%d %H:%M:%S') - Watching for changes in $WATCH_DIR" >> "$LOG_FILE"

exec /usr/bin/inotifywait -e create /var/www/paas/destroy-report | /bin/bash /var/www/paas-api/action-scripts/app_destroy.sh >> "$LOG_FILE" 2>&1 

