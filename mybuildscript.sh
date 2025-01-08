git pull
docker-compose down
sudo docker system prune -a -f
docker-compose up --build -d
sudo supervisorctl restart all
# docker logs -f paas-api