#!/bin/bash

# Step 0: Initialize
read event
echo "Rebuild App Event detected: $event"

sleep 5

# In this rebuild file, the extracted subdomain is re_subdomain hence no need to add re before subdomain again
# Step 1: Extract subdomain from the event
subdomain=$(echo "$event" | awk '{print $3}' | sed 's/^re_//; s/.sh$//')
echo "Extracted subdomain: $subdomain"

# Step 2: Remove the Docker container
echo "Step 5: Stopping and removing Docker container..."
docker stop ${subdomain}-app 2>/dev/null
docker rm ${subdomain}-app 2>/dev/null
echo "Docker container stopped and removed: ${subdomain}-app"

# Step 3: Delete Docker image and prune
echo "Step 6: Deleting Docker image..."
docker rmi ${subdomain} 2>/dev/null
echo "Docker image deleted: ${subdomain}"
docker system prune -a -f

#STEP 4: Build Docker image and deploy container
sudo cp /var/www/paas/rebuild-report/"re_$subdomain.sh" /var/www/paas/deployed_apps/"$subdomain"/
sudo chmod +x /var/www/paas/deployed_apps/"$subdomain"/"re_$subdomain.sh"
echo "Copying /var/www/paas/rebuild-report/re_$subdomain.sh to /var/www/paas/deployed_apps/$subdomain/"

sudo sh -x "/var/www/paas/deployed_apps/$subdomain/re_$subdomain.sh" &> /var/www/paas/logs/$subdomain/rebuild.log
echo "Now rebuilding the application docker container."


# Final Step: Completion message
echo "Re-Deploy Application completed successfully for subdomain: ${subdomain}."
