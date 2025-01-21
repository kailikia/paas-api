git pull
docker-compose down
sudo docker system prune -a -f
docker-compose up --build -d
sudo supervisorctl restart all
# tail -f /var/log/supervisor/paas_supervisor_stdout.log
# acme.sh --issue -d doman.techcamp.app --nginx

# ~/.acme.sh/acme.sh --issue --nginx --nginx-conf /etc/nginx/sites-available -d "yves.techcamp.app"
# find /home/user/myfolder/ -mindepth 1 -exec rm -rf {} +
# sudo lsof -t -c nginx
# sudo systemctl start nginx

# docker logs -f paas-api