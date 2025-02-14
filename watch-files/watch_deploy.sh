#!/bin/bash

WATCH_DIR="/var/www/paas/success-report"
SCRIPT_TO_RUN="/var/www/paas-api/action-scripts/app_deployment.sh"

/usr/bin/inotifywait -e create "$WATCH_DIR" && /bin/bash "$SCRIPT_TO_RUN"

done


