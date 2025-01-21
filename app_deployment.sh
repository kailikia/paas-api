#!/bin/bash

read event

echo "Deploy App Event detected: $event"

sleep 5

#STEP 1: Extract subdomain from the event (assuming it's the 3rd field in the event) and create logs directory
subdomain=$(echo "$event" | awk '{print $3}' | sed 's/.sh$//')
echo "Extracted subdomain: $subdomain"
sudo mkdir -p /var/www/paas/logs/$subdomain
sudo chmod +x /var/www/paas/logs/$subdomain

#STEP 2: Issue and Install ACME Certificates for the subdomain
sudo ~/.acme.sh/acme.sh --issue -d $subdomain.techcamp.app --standalone &> /var/www/paas/logs/$subdomain/issue-acme-cert.log
sudo ~/.acme.sh/acme.sh --install-cert --domain $subdomain.techcamp.app --ecc --key-file /root/.acme.sh/$subdomain.techcamp.app_ecc/$subdomain.techcamp.app.key --fullchain-file /root/.acme.sh/$subdomain.techcamp.app_ecc/fullchain.cer &> /var/www/paas/logs/$subdomain/install-acme-cert.log

#STEP 3: Copy the sh file from success report with docker steps, into the deployed apps folder
sudo cp /var/www/paas/success-report/"$subdomain.sh" /var/www/paas/deployed_apps/"$subdomain"/
sudo chmod +x /var/www/paas/deployed_apps/"$subdomain"/"$subdomain.sh"
echo "Copying /var/www/paas/success-report/$subdomain.sh to /var/www/paas/deployed_apps/$subdomain/"

#STEP 4: Build Docker image and deploy container
echo "Now deploying Docker"
sudo sh -x "/var/www/paas/deployed_apps/$subdomain/$subdomain.sh" &> /var/www/paas/logs/$subdomain/docker.log
echo "Docker deployment completed successfully."

#STEP 5: Copy Nginx config files to sites-available directory
sudo cp -r /var/www/paas/deployed_nginx_files/* /etc/nginx/sites-available/
sudo chmod +x /etc/nginx/sites-available/"$subdomain.techcamp.app"
echo "Copying Nginx Files"

#STEP 6: Symlink to sites-enabled
sudo ln -s /etc/nginx/sites-available/"$subdomain.techcamp.app" /etc/nginx/sites-enabled/
sudo chmod +x /etc/nginx/sites-enabled/"$subdomain.techcamp.app"
echo "Copying /etc/nginx/sites-available/$subdomain.techcamp.app to /etc/nginx/sites-enabled/"

#STEP 7: Stop and Start Nginx Service or Kill nginx process and start NGINX
# sudo kill $(sudo lsof -t -c nginx)
# sudo systemctl start nginx
# echo "Nginx processes killed and NGINX started"

# Output event detection information
echo "Event ended"
