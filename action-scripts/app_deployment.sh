#!/bin/bash

read event

echo "Deploy App Event detected: $event"

sleep 5

#STEP 1: Extract subdomain from the event (assuming it's the 3rd field in the event) and create logs directory
subdomain=$(echo "$event" | awk '{print $3}' | sed 's/.sh$//')
echo "Extracted subdomain: $subdomain"
sudo mkdir -p /var/www/paas/logs/$subdomain
sudo chmod +x /var/www/paas/logs/$subdomain

# UPDATE THE JSON FILE FOR STATUS of DEPLOYMENT
JSON_FILE="/var/www/paas/deployed_apps_logs/$subdomain-server.json"
sudo chown root:root "$JSON_FILE"
chmod +x "$JSON_FILE"

#STEP 2: Issue and Install ACME Certificates for the subdomain
sudo systemctl stop nginx
sudo ~/.acme.sh/acme.sh --issue -d $subdomain.techcamp.app --standalone &> /var/www/paas/logs/$subdomain/issue-acme-cert.log
sudo ~/.acme.sh/acme.sh --install-cert --domain $subdomain.techcamp.app --ecc --key-file /root/.acme.sh/$subdomain.techcamp.app_ecc/$subdomain.techcamp.app.key --fullchain-file /root/.acme.sh/$subdomain.techcamp.app_ecc/fullchain.cer &> /var/www/paas/logs/$subdomain/install-acme-cert.log
sudo systemctl start nginx
echo "ACME Certificates issued and installed for $subdomain.techcamp.app"

# jq '.acme = "ACME Certificates issued and installed for $subdomain.techcamp.app" ' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"
jq --arg sub "$subdomain" '.acme = "ACME Certificates issued and installed for \($sub).techcamp.app"' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"


#STEP 3: Copy the sh file from success report with docker steps, into the deployed apps folder
sudo cp /var/www/paas/success-report/"$subdomain.sh" /var/www/paas/deployed_apps/"$subdomain"/
sudo chmod +x /var/www/paas/deployed_apps/"$subdomain"/"$subdomain.sh"
echo "Copying /var/www/paas/success-report/$subdomain.sh to /var/www/paas/deployed_apps/$subdomain/"

jq --arg msg "Copying the success-report file" '.["success-report"] = $msg' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"


#STEP 4: Build Docker image and deploy container
echo "Now deploying Docker"
sudo sh -x "/var/www/paas/deployed_apps/$subdomain/$subdomain.sh" &> /var/www/paas/logs/$subdomain/docker.log
echo "Docker deployment completed successfully."

jq --arg msg "Docker deployment completed successfully" '.docker = $msg' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"


#STEP 5: Copy Nginx config files to sites-available directory
sudo cp -r /var/www/paas/deployed_nginx_files/"$subdomain.techcamp.app" /etc/nginx/sites-available/
sudo chmod +x /etc/nginx/sites-available/"$subdomain.techcamp.app"
echo "Copying Nginx Files"

jq --arg msg "Nginx files copied to sites-available directory" '.["nginx-files"] = $msg' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"


#STEP 6: Symlink to sites-enabled
sudo ln -sf /etc/nginx/sites-available/"$subdomain.techcamp.app" /etc/nginx/sites-enabled/
sudo chmod +x /etc/nginx/sites-enabled/"$subdomain.techcamp.app"
echo "Copying /etc/nginx/sites-available/$subdomain.techcamp.app to /etc/nginx/sites-enabled/"

jq --arg msg "Symlink created for the sites-available" '.symlink = $msg' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"


#STEP 7: Reload Nginx 
sudo systemctl restart nginx
# echo "Reload NGINX "

jq --arg msg "Restarted Nginx" '.restart = $msg' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"


# Output event detection information
echo "Event ended"

jq --arg msg "true" '.complete = $msg' "$JSON_FILE" > tmp.json && mv tmp.json "$JSON_FILE"
