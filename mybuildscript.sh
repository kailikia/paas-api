git pull
docker-compose down
sudo docker system prune -a -f
docker-compose up --build -d
# sudo supervisorctl restart all
# acme.sh --config-home /root/.acme.sh --issue -d vedi.techcamp.app --standalone --cert-home /etc/nginx/ssl/vedi.techcamp.app
# tail -f /var/log/supervisor/paas_supervisor_stdout.log
# acme.sh --issue -d doman.techcamp.app --nginx
# find -mindepth 1 -exec rm -rf {} +
# sudo lsof -t -c nginx
# sudo systemctl start nginx
# sudo pkill -9 nginx


# docker logs -f paas-api