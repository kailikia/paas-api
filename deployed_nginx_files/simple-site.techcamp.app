
        server {   listen 80;
            server_name simple-site.techcamp.app;

            root /deployed_apps/simple-site;  

            index index.html;

            location / {
                try_files $uri $uri/ =404;
            }
        }
    