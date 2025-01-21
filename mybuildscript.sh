git pull
docker-compose down
sudo docker system prune -a -f
docker-compose up --build -d
sudo supervisorctl restart all
tail -f /var/log/supervisor/paas_supervisor_stdout.log
# ~/.acme.sh/acme.sh --issue --nginx -d "yves.techcamp.app"
# ~/.acme.sh/acme.sh --issue --nginx --nginx-conf /etc/nginx/sites-available -d "yves.techcamp.app"

# docker logs -f paas-api