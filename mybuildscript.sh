git pull
docker-compose down
sudo docker system prune -a -f
docker-compose up --build -d
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

# acme.sh --config-home /root/.acme.sh --issue -d vedi.techcamp.app --standalone --cert-home /etc/nginx/ssl/vedi.techcamp.app
# tail -f /var/log/supervisor/paas_supervisor_stdout.log
# tail -f /var/www/paas/logs/deploy_supervisor_stdout.log
# sudo tail -f /var/log/supervisor/supervisord.log

# /bin/bash -c "/usr/bin/inotifywait -e create /var/www/paas/success-report | /bin/bash /var/www/paas-api/action-scripts/app_deployment.sh" >> "$LOG_FILE" 2>&1 

# acme.sh --issue -d doman.techcamp.app --nginx
# find -mindepth 1 -exec rm -rf {} +
# sudo lsof -t -c nginx
# sudo systemctl start nginx
# sudo pkill nginx
# sudo pkill inotifywait
# pgrep -fl inotifywait


# docker logs -f paas-api