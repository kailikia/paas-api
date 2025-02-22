#!/bin/bash

WATCH_DIR="/var/www/paas/rebuild-report"
SCRIPT_TO_RUN="/var/www/paas-api/action-scripts/app_rebuild.sh"
LOG_FILE="/var/log/supervisor/paas_supervisor_stdout.log"


echo "$(date '+%Y-%m-%d %H:%M:%S') - Watching for changes in $WATCH_DIR" >> "$LOG_FILE"

if pgrep -f inotifywait > /dev/null; then
    echo "Inotify is already running. Exiting." >> "$LOG_FILE"
    exit 1
fi

/usr/bin/inotifywait -e create /var/www/paas/rebuild-report | /bin/bash /var/www/paas-api/action-scripts/app_rebuild.sh >> "$LOG_FILE" 2>&1 




