#!/bin/bash

# Step 0: Initialize
read event
echo "Deploy App Event detected: $event"

# Step 1: Extract subdomain from the event
subdomain=$(echo "$event" | awk '{print $3}' | sed 's/.sh$//')
echo "Extracted subdomain: $subdomain"
mkdir -p /var/www/logs/$subdomain
echo "Created logs directory: /var/www/logs/$subdomain"

# Step 2: Define app name
APP_NAME="techcamp.app"

# Step 3: Delete files and folders
echo "Step 3: Deleting files and folders..."

delete_if_exists() {
    if [ -e "$1" ]; then
        rm -rf "$1"
        echo "Deleted: $1"
    else
        echo "Not found: $1"
    fi
}

# Allow the owner (root) full access to the directories
sudo chmod -R u+rwx /root/.acme.sh
sudo chmod -R u+rwx /etc/nginx/sites-available
sudo chmod -R u+rwx /etc/nginx/sites-enabled
sudo chmod -R u+rwx /var/www/paas

# Call delete_if_exists for each file or folder
delete_if_exists "/root/.acme.sh/${subdomain}.${APP_NAME}_ecc"
delete_if_exists "/etc/nginx/sites-available/${subdomain}.${APP_NAME}"
delete_if_exists "/etc/nginx/sites-enabled/${subdomain}.${APP_NAME}"
delete_if_exists "/var/www/paas/deployed_apps/${subdomain}"
delete_if_exists "/var/www/paas/deployed_nginx_files/${subdomain}.${APP_NAME}"
delete_if_exists "/var/www/paas/logs/${subdomain}"
delete_if_exists "/var/www/paas/success-report/${subdomain}.sh"
delete_if_exists "/var/www/paas/deployed_app_logs/${subdomain}.json"

# Step 4: Delete record from the database
echo "Step 4: Deleting record from database..."
# Add your database deletion commands here
echo "Database record deletion (if any) completed for ${subdomain}."

# Step 5: Remove Docker container
echo "Step 5: Stopping and removing Docker container..."
docker stop ${subdomain}-app 2>/dev/null
docker rm ${subdomain}-app 2>/dev/null
echo "Docker container stopped and removed: ${subdomain}-app"

# Step 6: Delete Docker image and prune
echo "Step 6: Deleting Docker image..."
docker rmi ${subdomain} 2>/dev/null
echo "Docker image deleted: ${subdomain}"
docker system prune -a -f

# Final Step: Completion message
echo "Application removal completed successfully for subdomain: ${subdomain}."
