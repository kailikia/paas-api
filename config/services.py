import os
from config.models import Subdomain, create_engine, Base, sessionmaker
import subprocess, sys 
from digitalocean import Domain
import digitalocean
import shutil
import platform


DOTOKEN="dop_v1_d69f07ab5768ed0ebb16254bc3566fd107921ca154f1d06de8d8f26f4c66bbe3"
deploy_domain = "techcamp.app"

engine = create_engine("sqlite:///config/paas.db", connect_args={'check_same_thread': False})
Base.metadata.create_all(bind=engine)
session = sessionmaker(bind=engine)
session = session()

#Service Functions
def digital_ocean_create_subdomain(subdomain):
    domain = digitalocean.Domain(token=DOTOKEN, name=deploy_domain)
    records = domain.get_records()
    for r in records:
        print(r.type, r.data)

    manager = digitalocean.Manager(token=DOTOKEN)
    my_projects = manager.get_all_projects()
    resources = my_projects[0].get_all_resources()
    return resources

def add_subdomain(name,user):
      add_domain = Subdomain(name, user)
      return add_domain

def deploy_ssh_subprocess(github_url, subdomain):
    error_in_step = 0
    #In windows RUN POWERSHELL AS ADMIN and run command "Set-ExecutionPolicy RemoteSigned"

    #1. Write the deployment in a txt file with the name deploy_subdomain.txt. Echo a final text in the end to 
    # check IF statement

    #2. Create a new route that is reading that txt file

    #3. Check the route every 5 secs, check if error_in_step has changed to stop. Check in frontend to show progress in deploy_steps variable above

    #Change directory
    # os.chdir('deployed_apps')

    if os.path.exists(subdomain):
        shutil.rmtree(subdomain)  # Remove the existing subdomain directory

    #check size of file uploaded. If 
    clone_path = os.path.join(subdomain, 'app')
    # git_subdomain= 'git clone https://github.com/kailikia/paas-app.git' + " "+ destination_path
    git_subdomain= f'git clone {github_url}' + " "+ clone_path 

    config_dir = os.path.dirname(os.path.abspath(__file__)) 
    logs_dir = os.path.dirname(config_dir)    
    deploy_subdomain_logs = "../deployed_apps_logs", subdomain+".txt"

    #Delete existing log contents
    open(deploy_subdomain_logs, 'w+').close()

    #initiate empty list in logs
    with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('[')

    #STEP 1: change directory to deployed_apps for subdomain
    if os.path.isdir(subdomain):
        #Delete existing subdomain project 
        os.system('rmdir /S /Q "{}"'.format(subdomain))
        # Check if the subdomain directory exists
        
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('{"step" : 1, "message" : "Subdomain Domain Created for ' + subdomain+'"}')
    else:
        #Clone project    
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('{"step" : 1, "message" : "Subdomain Domain Re-Created for '+ subdomain +'"}')


    #STEP 2: Clone into subdomain app directory
    if subprocess.run(git_subdomain, shell=True).returncode == 0:
        #Edit txt to : Project cloned successfully 
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 2, "message" : "Project '+subdomain +' cloned successfully"}')

    else:
        myfile.write(',{"step" : 2, "message" : "Error cloning project '+subdomain +'."}')


    #STEP 3: app folder inside it, Change permission to modify delete .git,Procfile, .gitignore files
    try:
        file_path = os.path.join(subdomain,'app') 
        os.chmod(file_path, 0o777)  

        for root, dirs, files in os.walk(subdomain):
            for file in files:
                if file == 'requirements.txt':
                    os.remove(os.path.join(root, file))
                if file == 'Procfile':
                    os.remove(os.path.join(root, file))
                if file == '.gitignore':
                    os.remove(os.path.join(root, file))
                # if file == '.git':
                #     os.remove(os.path.join(root, file))

        with open(deploy_subdomain_logs, "a") as myfile:
                myfile.write(',{"step" : 3, "message" : "Project '+subdomain +' copied into app folder successfully"}')

    except :
        myfile.write(',{"step" : 3, "message" : "Error copying project '+subdomain +' into app folder ."}')


    #STEP 4 : Then copy generic requirements.txt, Dockerfile, docker-compose and mybuildscript.sh
    config_files = ["requirements.txt", "Dockerfile", "docker-compose.yml", "mybuildscript.sh"]  
    script_dir = os.path.dirname(os.path.abspath(__file__))     #config folder path
    parent_dir = os.path.dirname(script_dir)                    #root path

    try:
        for file_name in config_files:
            src_file = os.path.join(parent_dir, file_name)
            dest_file = os.path.join(subdomain, file_name)
            shutil.copy(src_file, dest_file)

        with open(deploy_subdomain_logs, "a") as myfile:
                myfile.write(',{"step" : 4, "message" : "Project '+subdomain +' [requirements.txt, Dockerfile, docker-compose and mybuildscript.sh] files added successfully"}')

    except :
        myfile.write(',{"step" : 4, "message" : "Error adding [requirements.txt, Dockerfile, docker-compose and mybuildscript.sh] files to project '+subdomain +'."}')


    #STEP 5 : Create an nginx string with variables {port} {subdomain} concatenated and add to an ngix-config file.
    #call the file subdomain.techcamp.app. Add it to etc/nginx/sites-available.
    if platform.system() == 'Linux':

        files = os.listdir('deployed_apps_logs')
        # Count the number of files (excluding directories)
        file_count = sum(1 for file_name in files if os.path.isfile(os.path.join( logs_dir, 'deployed_apps_logs', file_name)))
        port = 5001 + file_count

        # Define the Nginx configuration content with variables
        nginx_config = f"""
            server {{
                server_name {subdomain}.techcamp.app;

                location /{{
                    proxy_pass http://46.101.2.132:{port};
                    }}
                
                # Your additional Nginx configuration goes here

            }}

            """
        nginx_config_path = f"../etc/nginx/conf.d/{subdomain}"
        try:
            with open(nginx_config_path, 'w') as config_file:
                config_file.write(nginx_config)

            with open(deploy_subdomain_logs, "a") as myfile:
                myfile.write(',{"step" : 5, "message" : "Nginx server block for '+subdomain +'.techcamp.app file created."}')

        except OSError as e:
             myfile.write(',{"step" : 5, "message" : "Error adding Nginx server block for '+subdomain +'.techcamp.app"}')

    else :
        myfile.write(',{"step" : 5, "message" : "Error configuring project '+subdomain +'. "}')

    #STEP 6 : Test and  Refresh the nginx.
    try:
        sites_enabled_path = "../etc/nginx/nginx.conf"
        if os.path.exists(nginx_config_path):
            # Create a symbolic link in sites-enabled
            site_enabled_link = os.path.join(sites_enabled_path, subdomain)
            
            try:
                os.symlink(nginx_config_path, site_enabled_link)
                print(f"Enabled site: {subdomain}")

                # Reload Nginx to apply the configuration changes
                if os.system("sudo nginx -t") == 0:
                    os.system("sudo systemctl reload nginx")
                    print("Nginx reloaded successfully.")

                with open(deploy_subdomain_logs, "a") as myfile:
                    myfile.write(',{"step" : 6, "message" : "Project '+subdomain +' web server test successful"}')

            except OSError as e:
                print(f"Error creating symbolic link or reloading Nginx: {e}")
        else:
            print(f"Site configuration file '{subdomain}' not found in sites-available.")

       
    except :
        myfile.write(',{"step" : 6, "message" : "Error reloading web server project '+subdomain +'."}')


    #STEP 7 : Run mybuildscript.sh
    script_path = os.path.join(subdomain, "mybuildscript.sh")

    try:
        # Run the shell script using subprocess
        subprocess.run(["chmod", "+x", script_path], check=True)
        subprocess.run(["bash", script_path], check=True)
        print("Shell script executed successfully.")

        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 7, "message" : "Access Project '+subdomain +' at this link  '+subdomain+'.techcamp.app "}')

    except subprocess.CalledProcessError as e:
        print(f"Error running the shell script: {e}")
    except FileNotFoundError:
        print(f"The shell script file '{script_path}' was not found.")

    except:
        myfile.write(',{"step" : 7, "message" : "Docker error for project '+subdomain +'."}')


    #Milestone Task: Write and log in myfile as above
    #It was supposed to mount from step 3. Then it appears in our host machine in deployed apps with all data in app folder.
    #Then initiate an event call in linux then we do step 4 to 7 in the host machine.
    #step 3.2: build docker file with sudbomain name
    #step 3.3: run container using docker image created using subdomain

    #Close Log file and RETURN BACK TO ROUTE
    with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(']')


    os.chdir('..')

    return True