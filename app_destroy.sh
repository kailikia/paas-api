#!/bin/bash

# Step 0: Initialize
read event
echo "Deploy App Event detected: $event"

# Step 1: Extract subdomain from the event (assuming it's the 3rd field in the event) and create logs directory
subdomain=$(echo "$event" | awk '{print $3}' | sed 's/.sh$//')
echo "Extracted subdomain: $subdomain"
mkdir -p /var/www/logs/$subdomain
echo "Created logs directory: /var/www/logs/$subdomain"

# Step 2: Define app name
APP_NAME="techcamp.app"

# Step 3: Delete files and folders
echo "Step 3: Deleting files and folders..."
sudo sudo rm -rf /root/.acme.sh/${subdomain}.${APP_NAME}_ecc
echo "Deleted: /root/.acme.sh/${subdomain}.${APP_NAME}_ecc"

sudo sudo rm -f /etc/nginx/sites-available/${subdomain}.${APP_NAME}
echo "Deleted: /etc/nginx/sites-available/${subdomain}.${APP_NAME}"

sudo rm -f /etc/nginx/sites-enabled/${subdomain}.${APP_NAME}
echo "Deleted: /etc/nginx/sites-enabled/${subdomain}.${APP_NAME}"

sudo rm -rf /var/www/paas/deployed_apps/${subdomain}
echo "Deleted: /var/www/paas/deployed_apps/${subdomain}"

sudo rm -f /var/www/paas/deployed_nginx_files/${subdomain}.${APP_NAME}
echo "Deleted: /var/www/paas/deployed_nginx_files/${subdomain}.${APP_NAME}"

sudo rm -rf /var/www/logs/${subdomain}
echo "Deleted: /var/www/logs/${subdomain}"

sudo rm -f /var/www/paas/success-report/${subdomain}.sh
echo "Deleted: /var/www/paas/success-report/${subdomain}.sh"

sudo rm -f /var/www/paas/deployed_app_logs/${subdomain}.json
echo "Deleted: /var/www/paas/deployed_app_logs/${subdomain}.json"

# Step 4: Delete record from the database
echo "Step 4: Deleting record from database..."
# Add your database deletion commands here
# Example: mysql -u user -p -e "DELETE FROM table_name WHERE subdomain='${subdomain}';"
echo "Database record deletion (if any) completed for ${subdomain}."

# Step 5: Remove Docker container
echo "Step 5: Stopping and removing Docker container..."
docker stop ${subdomain}-app
docker sudo rm ${subdomain}
echo "Docker container stopped and removed: ${subdomain}"

# Step 6: Delete Docker image
echo "Step 6: Deleting Docker image..."
docker sudo rmi ${subdomain}
echo "Docker image deleted: ${subdomain}"

# Final Step: Completion message
echo "Application removal completed successfully for subdomain: ${subdomain}."
