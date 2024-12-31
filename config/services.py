import os
from config.models import DeployedApplication, Subdomain, create_engine, Base, sessionmaker
import subprocess, sys 
import digitalocean
import shutil, json
from pydo import Client


DOTOKEN=os.getenv("DO_TOKEN")
deploy_domain = "techcamp.app"

engine = create_engine("sqlite:///database/paas.db", connect_args={'check_same_thread': False})
Base.metadata.create_all(bind=engine)
session = sessionmaker(bind=engine)
session = session()

# client = Client(token=os.environ.get("DO_TOKEN"))
client = Client(DOTOKEN)

def get_subdomain_logs(subdomain):
    try:

        cur_path = "/app/deployed_apps"

        os.chdir(cur_path)

        if os.path.exists(cur_path):

            deploy_subdomain_logs = os.path.join("../deployed_apps_logs", subdomain +".json")
            print("Subdomain Logs----------------", deploy_subdomain_logs)

            #Check if the file exists
            if os.path.exists(deploy_subdomain_logs):
                # Open and read the file content
                with open(deploy_subdomain_logs, 'r') as file:
                    file_content = file.read()
                    return json.loads(file_content)  # Assuming the file contains JSON data
            else:
                return {"Error": "Log file does not exist."}
            return deploy_subdomain_logs
            
        else:
            return {"Error": "Deployed app path doesn't exist." + cur_path }
    except Exception as e:
        return {"Error" : str(e)}

#Service Functions
def digital_ocean_list_domains():
    resp = client.domains.list()
    print("DO List-------",resp)
    return resp
   
     
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

def add_deployed_apps(subdomain_id,github_url,port):
      add_app = DeployedApplication(subdomain_id, github_url, port)
      return add_app

def deploy_html_by_ssh_subprocess(github_url, subdomain, user):
    error_in_step = 0
    #In windows RUN POWERSHELL AS ADMIN and run command "Set-ExecutionPolicy RemoteSigned"

    cur_path = "/app/deployed_apps"

    os.chdir(cur_path)

    # if os.path.exists(cur_path):
    # os.chdir(os.getcwd()+'/deployed_apps')
    clone_path = os.path.join(subdomain)

    git_url_for_subdomain= f"git clone --depth 1 {github_url} {clone_path} "
    deploy_subdomain_logs = os.path.join("../deployed_apps_logs", subdomain +".json")

    print("Subdomain Logs----------------", deploy_subdomain_logs)

    #Delete existing log contents
    open(deploy_subdomain_logs, 'w+').close()

    #initiate empty list in logs
    with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('[')

    #STEP 1: Change location to deployed apps directory in subdomain folder
    if session.query(Subdomain).filter(Subdomain.name==subdomain.strip().lower()).first() == None:
        #Delete existing subdomain project 
        # os.system('rmdir /S /Q "{}"'.format(subdomain))

        # def remove_contents(directory):
        #     shutil.rmtree(directory)
            
        # remove_contents(subdomain)
        #2. Save subdomain in DB
        session.add(add_subdomain(subdomain,user))
        session.commit()
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('{"step" : 1, "message" : "Subdomain Domain Created for ' + subdomain+'"}')

        print("Step 1: Location changed to subdomain folder and domain created--------------", subdomain, os.getcwd())
    else:  
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('{"step" : 1, "message" : "Subdomain Domain Re-Created for '+ subdomain +'"}')

    #STEP 2: Clone into subdomain app directory
    if subprocess.run(git_url_for_subdomain, shell=True).returncode == 0:
        #Edit txt to : Project cloned successfully 
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 2, "message" : "Project '+subdomain +' cloned successfully"}')
        print("Step 2: Git Cloned Successfull-----------------")
    else:
        myfile.write(',{"step" : 2, "message" : "Error cloning project '+subdomain +'."}')

    #STEP 3: Change subdomain folder permission to modify. Delete .git folder and .gitignore files
    try:
        def change_permissions(file_path, mode):
            os.chmod(file_path, mode)
        mode = 0o777
        folder_path = os.path.join(subdomain) 
        git_folder_path = os.path.join(folder_path, '.git')

        change_permissions(git_folder_path, mode)
        
        # os.chmod(git_folder_path, 0o777) 
        
        if os.path.exists(git_folder_path):
            shutil.rmtree(git_folder_path)
            print(f"The .git folder in {folder_path} has been removed.")
        else:
            print(f"The .git folder in {folder_path} does not exist.")


        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 3, "message" : "Change permissions for '+subdomain +' successful."}')

        print("Step 3: Permission built for subdomain folder-----------------")
    except :
        myfile.write(',{"step" : 3, "message" : "Error changing permission for '+subdomain +' ."}')


    #STEP 4 : Create an nginx string with variables {port} {subdomain} concatenated and add to an ngix-config file.
    nginx_config = f"""
        server {{   listen 80;
            server_name {subdomain}.techcamp.app;

            root /deployed_apps/{subdomain};  

            index index.html;

            location / {{
                try_files $uri $uri/ =404;
            }}
        }}
    """
    deployed_nginx_subdomain_file = f"../deployed_nginx_files/{subdomain}.techcamp.app"

    try:
        with open(deployed_nginx_subdomain_file, 'w') as nginx_file:
            nginx_file.write(nginx_config)

        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 4, "message" : "Nginx server block for '+subdomain +'.techcamp.app file created."}')

    except OSError as e:
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 4, "message" : "Error adding Nginx server block for '+subdomain +'.techcamp.app"}')


    files = os.listdir('../deployed_apps_logs')
    # Count the number of files (excluding directories

    print("Step 4: NGINX Server File Created Successfully-----------------")

    #STEP 5: Add deployed apps

    file_count = sum(1 for file_name in files if os.path.isfile(os.path.join('../deployed_apps_logs', file_name)))
    port = 5001 + file_count

    subdomain_created = session.query(Subdomain).filter(Subdomain.name==subdomain.strip().lower()).first()
    print("Subdomain---------------", subdomain_created)
    session.add(add_deployed_apps(subdomain_created.id,github_url,port))
    session.commit()
 
    try:
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 5, "message" : "Deployed Apps Added to Database Successfully for '+subdomain +'.techcamp.app "}')
    except OSError as e:
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 5, "message" : "Error adding deployed apps to database for '+subdomain +'.techcamp.app"}')

    print("Step 5: Deployed Apps Added to Database Successfully-----------------")

       #Close Log file and RETURN BACK TO ROUTE
    with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(']')
            # myfile.close()

    os.chdir('..')

    return True

# def deploy_python_by_ssh_subprocess(github_url, subdomain, user):
#     error_in_step = 0
#     #In windows RUN POWERSHELL AS ADMIN and run command "Set-ExecutionPolicy RemoteSigned"

#     #1. Write the deployment in a txt file with the name deploy_subdomain.txt. Echo a final text in the end to 
#     # check IF statement

#     #2. Create a new route that is reading that txt file

#     #3. Check the route every 5 secs, check if error_in_step has changed to stop. Check in frontend to show progress in deploy_steps variable above

#     #Change directory
#     os.chdir(os.getcwd()+'//deployed_apps')

#     # clone_path = os.path.join(subdomain, 'app')

#     clone_path = os.path.join(subdomain)

#     git_url_for_subdomain= f"git clone --depth 1 {github_url} {clone_path} "
  
#     # deploy_subdomain_logs = "../deployed_apps_logs", subdomain+".txt"
#     deploy_subdomain_logs = os.path.join("../deployed_apps_logs", subdomain+".txt")

#     #Delete existing log contents
#     open(deploy_subdomain_logs, 'w+').close()

#     #initiate empty list in logs
#     with open(deploy_subdomain_logs, "a") as myfile:
#             myfile.write('[')

#     #STEP 1: Change location to deployed apps directory in subdomain folder
#     if os.path.isdir(subdomain):
#         #Delete existing subdomain project 
#         os.system('rmdir /S /Q "{}"'.format(subdomain))
#         #2. Save subdomain in DB
#         session.add(add_subdomain(subdomain,user))
#         session.commit()
        
#         with open(deploy_subdomain_logs, "a") as myfile:
#             myfile.write('{"step" : 1, "message" : "Subdomain Domain Created for ' + subdomain+'"}')
#     else:  
#         with open(deploy_subdomain_logs, "a") as myfile:
#             myfile.write('{"step" : 1, "message" : "Subdomain Domain Re-Created for '+ subdomain +'"}')


#     #STEP 2: Clone into subdomain app directory
#     if subprocess.run(git_url_for_subdomain, shell=True).returncode == 0:
 
#         #Edit txt to : Project cloned successfully 
#         with open(deploy_subdomain_logs, "a") as myfile:
#             myfile.write(',{"step" : 2, "message" : "Project '+subdomain +' cloned successfully"}')

#     else:
#         myfile.write(',{"step" : 2, "message" : "Error cloning project '+subdomain +'."}')


#     #STEP 3: Change subdomain folder permission to modify. Delete .git folder and .gitignore files
#     # try:
#         # file_path = os.path.join(subdomain,'app') 
#     file_path = os.path.join(subdomain) 
#     os.chmod(file_path, 0o777)  

#     for root, dirs, files in os.walk(subdomain):
#             print("Stuff inside folder:", root, dirs, files)
#             for file in files:
#                 # if file == 'requirements.txt':
#                 #     os.remove(os.path.join(root, file))
#                 # if file == 'Procfile':
#                 #     os.remove(os.path.join(root, file))
#                 if file == '.gitignore':
#                     os.remove(os.path.join(root, file))
#                 # if file == '.git':
#                 #     os.remove(os.path.join(root, file))

#     with open(deploy_subdomain_logs, "a") as myfile:
#         myfile.write(',{"step" : 3, "message" : "Change permissions for '+subdomain +' successful."}')

#     # except :
#     #     myfile.write(',{"step" : 3, "message" : "Error changing permission for '+subdomain +' ."}')


#     #STEP 4 : Then copy generic requirements.txt, Dockerfile, docker-compose and mybuildscript.sh
#         # config_files = ["requirements.txt", "Dockerfile", "docker-compose.yml", "mybuildscript.sh"]  
#         # script_dir = os.path.dirname(os.path.abspath(__file__))     #config folder path
#         # parent_dir = os.path.dirname(script_dir)                    #root path

#         # try:
#         #     for file_name in config_files:
#         #         src_file = os.path.join(parent_dir, file_name)
#         #         dest_file = os.path.join(subdomain, file_name)
#         #         shutil.copy(src_file, dest_file)

#         #     with open(deploy_subdomain_logs, "a") as myfile:
#         #             myfile.write(',{"step" : 4, "message" : "Project '+subdomain +' [requirements.txt, Dockerfile, docker-compose and mybuildscript.sh] files added successfully"}')

#         # except :
#         #     myfile.write(',{"step" : 4, "message" : "Error adding [requirements.txt, Dockerfile, docker-compose and mybuildscript.sh] files to project '+subdomain +'."}')


#     #STEP 5 : Create an nginx string with variables {port} {subdomain} concatenated and add to an ngix-config file.
#     #call the file subdomain.techcamp.app. Add it to etc/nginx/sites-available.

#     files = os.listdir('../deployed_apps_logs')
#     # Count the number of files (excluding directories)
#     file_count = sum(1 for file_name in files if os.path.isfile(os.path.join('../deployed_apps_logs', file_name)))
#     port = 5001 + file_count

#     subdomain = session.query(Subdomain).filter(Subdomain.name==subdomain.strip().lower()).one()

#     print("Subdomain---------------", subdomain)

#     session.add(add_deployed_apps(subdomain.id,github_url,port))
#     session.commit()

#     # Define the Nginx configuration content with variables
#     # nginx_config = f"""
#     #     server {{
#     #         server_name {subdomain}.techcamp.app;

#     #         location /{{
#     #             proxy_pass http://46.101.2.132:{port};
#     #             }}
            
#     #         # Your additional Nginx configuration goes here

#     #     }}
#     #     """

#     nginx_config = f"""
#         server {{   listen 80;
#             server_name {subdomain}.techcamp.app;

#             root /deployed_apps/{subdomain};  

#             index index.html;

#             location / {{
#                 try_files $uri $uri/ =404;
#             }}
#         }}
#     """

#     deployed_nginx_subdomain_file = f"../deployed_nginx_files/{subdomain}"
#     try:
#         with open(deployed_nginx_subdomain_file, 'w') as nginx_file:
#             nginx_file.write(nginx_config)

#         with open(deploy_subdomain_logs, "a") as myfile:
#             myfile.write(',{"step" : 5, "message" : "Nginx server block for '+subdomain +'.techcamp.app file created."}')

#     except OSError as e:
#         with open(deploy_subdomain_logs, "a") as myfile:
#             myfile.write(',{"step" : 5, "message" : "Error adding Nginx server block for '+subdomain +'.techcamp.app"}')


#     #STEP 6 : Run NGINX configuration and expose app files scripts and reload nginx.
#     # if platform.system() == 'Linux':

#         # try:
#         #     sites_available_path = "/etc/nginx/sites-available/"
#         #     if os.path.exists(deployed_nginx_files):
#         #         # Create a symbolic link in sites-enabled
#         #         site_enabled_link = os.path.join(sites_enabled_path, subdomain)
                
#         #         try:
#         #             os.symlink(nginx_files, site_enabled_link)
#         #             print(f"Enabled site: {subdomain}")

#         #             # Reload Nginx to apply the configuration changes
#         #             if os.system("sudo nginx -t") == 0:
#         #                 os.system("sudo systemctl reload nginx")
#         #                 print("Nginx reloaded successfully.")

#         #             with open(deploy_subdomain_logs, "a") as myfile:
#         #                 myfile.write(',{"step" : 6, "message" : "Project '+subdomain +' web server test successful"}')

#         #         except OSError as e:
#         #             print(f"Error creating symbolic link or reloading Nginx: {e}")
#         #     else:
#         #         print(f"Site configuration file '{subdomain}' not found in sites-available.")

        
#         # except :
#         #     with open(deploy_subdomain_logs, "a") as myfile:
#         #         myfile.write(',{"step" : 6, "message" : "Error reloading web server project '+subdomain +'."}')
#     # else:
#     #     with open(deploy_subdomain_logs, "a") as myfile:
#     #         myfile.write(',{"step" : 6, "message" : "Error youre not in a nginx server for project '+subdomain +'."}')


#     #STEP 7 : Run mybuildscript.sh
#     # if platform.system() == 'Linux':

#     #     script_path = os.path.join(subdomain, "mybuildscript.sh")

#     #     try:
#     #         # Run the shell script using subprocess
#     #         subprocess.run(["chmod", "+x", script_path], check=True)
#     #         subprocess.run(["bash", script_path], check=True)
#     #         print("Shell script executed successfully.")

#     #         with open(deploy_subdomain_logs, "a") as myfile:
#     #             myfile.write(',{"step" : 7, "message" : "Access Project '+subdomain +' at this link  '+subdomain+'.techcamp.app "}')

#     #     except subprocess.CalledProcessError as e:
#     #         print(f"Error running the shell script: {e}")
#     #     except FileNotFoundError:
#     #         print(f"The shell script file '{script_path}' was not found.")

#     #     except:
#     #         with open(deploy_subdomain_logs, "a") as myfile:
#     #             myfile.write(',{"step" : 7, "message" : "Docker error for project '+subdomain +'."}')
#     # else:
#     #     with open(deploy_subdomain_logs, "a") as myfile:
#     #             myfile.write(',{"step" : 7, "message" : "Docker error ,youre not running docker for project '+subdomain +'."}')


#     #Milestone Task: Write and log in myfile as above
#     #It was supposed to mount from step 3. Then it appears in our host machine in deployed apps with all data in app folder.
#     #Then initiate an event call in linux then we do step 4 to 7 in the host machine.
#     #step 3.2: build docker file with sudbomain name
#     #step 3.3: run container using docker image created using subdomain

#     #Close Log file and RETURN BACK TO ROUTE
#     with open(deploy_subdomain_logs, "a") as myfile:
#             myfile.write(']')


#     os.chdir('..')

#     return True