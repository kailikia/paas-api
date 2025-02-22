git pull
docker-compose down
sudo docker system prune -a -f
docker-compose up --build -d
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

