from datetime import datetime
import os
from config.models import DeployedApplication, Subdomain, create_engine, Base, sessionmaker
import subprocess, sys 
import digitalocean
import shutil, json, requests
from pydo import Client


DOTOKEN=os.getenv("DO_TOKEN")
deploy_domain = "techcamp.app"
ip_address = "134.209.24.19"
url = f"https://api.digitalocean.com/v2/domains/{deploy_domain}/records"

engine = create_engine("sqlite:///database/paas.db", connect_args={'check_same_thread': False})
Base.metadata.create_all(bind=engine)
session = sessionmaker(bind=engine)
session = session()

# client = Client(token=os.environ.get("DO_TOKEN"))
client = Client(DOTOKEN)

# Set up headers for authorization
headers = {
    "Authorization": f"Bearer {DOTOKEN}",
    "Content-Type": "application/json"
}

def digital_ocean_create_subdomain(subdomain):
    data = {
    "type": "A",  # A record type
    "name": subdomain,
    "data": ip_address,
    "ttl": 600  # Time to live in seconds
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print("Subdomain created successfully!---------------------", response.json())
    else:
        print("Failed to create subdomain.------------------------", response.status_code, response.json())


def digital_ocean_list_domains():
    resp = client.domains.list()
    print("DO List-------",resp)
    return resp


def digital_ocean_delete_subdomain(subdomain):
    
    try:
        client.domains.delete(domain_name=subdomain)

        print("Subdomain deleted from DO successfully!---------------------", subdomain)
    except Exception as e:
        print("Failed to delete subdomain from DO .------------------------", str(e))


# GET LOGS FUNCTIONS
def get_docker_logs(subdomain):
    try:
        log_path = "/app/subdomain_logs"

        os.chdir(log_path)
        parsed_logs = []

        if os.path.exists(log_path):
            dock_logs = os.path.join(f"/app/subdomain_logs/{subdomain}/docker.log")
            print("Subdomain Docker Logs----------------", dock_logs)

            #Check if the file exists
            if os.path.exists(dock_logs):
                # Open and read the file content
                with open(dock_logs, 'r') as file:
                    for line in file:
                        line = line.strip()  # Remove leading/trailing whitespace
                        if line:  # Skip empty lines
                            parsed_logs.append({"message": line})
                return json.dumps(parsed_logs, indent=4)
            else:
                return {"Error": "Log file does not exist."}
            
        else:
            return {"Error": "Deployed app path doesn't exist." + log_path }


    except Exception as e:
        return {"Error" : str(e)}


def get_nginx_logs(subdomain):

    try:
        log_path = "/app/subdomain_logs"

        os.chdir(log_path)
        parsed_logs = []

        if os.path.exists(log_path):
            nginx_logs = os.path.join(f"/app/subdomain_logs/{subdomain}/nginx_access.log")
            print("Nginx Logs----------------", nginx_logs)

            #Check if the file exists
            if os.path.exists(nginx_logs):
                # Open and read the file content
                with open(nginx_logs, 'r') as file:
                    for line in file:
                        line = line.strip()  # Remove leading/trailing whitespace
                        if line:  # Skip empty lines
                            parsed_logs.append({"message": line})
                return json.dumps(parsed_logs, indent=4)
            else:
                return {"Error": "Log file {} does not exist."}
            
        else:
            return {"Error": "Deployed app path doesn't exist." + log_path }

    except Exception as e:
        return {"Error" : str(e)}


def get_acme_logs(sub):

    try:
        log_path = "/app/subdomain_logs"

        os.chdir(log_path)
        parsed_logs = []

        if os.path.exists(log_path):
            acme_logs = os.path.join(f"/app/subdomain_logs/{sub}/issue-acme-cert.log")
            print("Acme Logs----------------", acme_logs)

            #Check if the file exists
            if os.path.exists(acme_logs):
                # Open and read the file content
                with open(acme_logs, 'r') as file:
                    for line in file:
                        line = line.strip()  # Remove leading/trailing whitespace
                        if line:  # Skip empty lines
                            parsed_logs.append({"message": line})
                return json.dumps(parsed_logs, indent=4)            
            else:
                return {"Error": f"Log file {acme_logs} does not exist."}
             
        else:
            return {"Error": "Deployed app path doesn't exist." + log_path }

    except Exception as e:
        return {"Error" : str(e)}


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
            return {"Error": "Deployed app logs path doesn't exist." + cur_path }
    except Exception as e:
        return {"Error" : str(e)}


def get_server_logs(subdomain):
    try:

        cur_path = "/app/deployed_apps"

        os.chdir(cur_path)

        if os.path.exists(cur_path):
            deploy_server_logs = os.path.join("../deployed_apps_logs", subdomain +"-server.json")
            print("Server Logs Path----------------", deploy_server_logs)

            #Check if the file exists
            if os.path.exists(deploy_server_logs):
                # Open and read the file content
                
                with open(deploy_server_logs, 'r') as file:
                    file_content = file.read()
                    return json.loads(file_content)  # Assuming the file contains JSON data
            else:
                return {"Error": "Log file does not exist ..." + deploy_server_logs}
            return deploy_server_logs
        else:
            return {"Error": "Deployed app logs path doesn't exist." + deploy_server_logs }
    except Exception as e:
        return {"Error" : str(e)}


# Service DB Functions
def add_subdomain(name,user):
      add_domain = Subdomain(name, user)
      return add_domain

def add_deployed_apps(subdomain_id,github_url,port):
      add_app = DeployedApplication(subdomain_id, github_url, port)
      return add_app

def delete_subdomain_and_apps_by_name(subdomain_name):
    try:
        # Query the subdomain by name
        subdomain = session.query(Subdomain).filter(Subdomain.name == subdomain_name).first()
        if not subdomain:
            print(f"Subdomain '{subdomain_name}' not found!")
            return
        # Delete associated deployed applications
        session.query(DeployedApplication).filter(DeployedApplication.subdomain_id == subdomain.id).delete()
        # Delete the subdomain
        session.delete(subdomain)
        # Commit the transaction
        session.commit()
        print(f"Subdomain '{subdomain_name}' and associated applications deleted successfully!")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()

    return True


# Deploy and Server Functions 

def deploy_html_by_ssh_subprocess(github_url, subdomain, user, choice):
    error_in_step = 0
    #In windows RUN POWERSHELL AS ADMIN and run command "Set-ExecutionPolicy RemoteSigned"

    cur_path = "/app/deployed_apps"
    
    os.chdir(cur_path)

    # if os.path.exists(cur_path):
    clone_path = os.path.join(subdomain)

    git_url_for_subdomain= f"git clone --depth 1 {github_url} {clone_path} "
    deploy_subdomain_logs = os.path.join("../deployed_apps_logs", subdomain +".json")
    print("Subdomain Logs----------------", deploy_subdomain_logs)

    # ADD DEPLOY SERVER LOGS JSON FILE
    deploy_server_logs = os.path.join("../deployed_apps_logs", subdomain +"-server.json")
    
    server_file = {
        "subdomain": str(subdomain),  
        "acme": "",
        "docker": "",
        "success-report": "",
        "nginx-files": "",
        "symlink": "",
        "restart": "",
        "complete": False 
    }


    # Write JSON safely using a temp file
    temp_file = deploy_server_logs + ".tmp"
    with open(temp_file, "w") as servfile:
        json.dump(server_file, servfile, indent=4)

    # Debugging: Print JSON before writing
    print("Generated JSON:", json.dumps(server_file, indent=4))

    # Rename it back to .json safely to avoid race conditions
    os.rename(temp_file, deploy_server_logs)

    print("Server Subdomain Logs Json File Created -------------------------------------", deploy_server_logs)

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


    #STEP to Copy Dockerfile to deployed apps and get port number
    if choice == 'flask':
        try:
            flask_files = f"cp /app/flask_apps_requirements/* /app/deployed_apps/{subdomain}"

            # Execute the command
            subprocess.run(flask_files, check=True, shell=True)
            print(f"Docker File copied successfully to {subdomain}.-------------------")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}----------------------------------------")
        
    elif choice == 'html':
        try:
            html_files = f"cp /app/html_apps_requirements/Dockerfile /app/deployed_apps/{subdomain}"

            # Execute the command
            subprocess.run(html_files, check=True, shell=True)
            print(f"Docker File copied successfully to {subdomain}.-------------------")
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}----------------------------------------")
        

    files = os.listdir('../deployed_apps_logs')
    # Count the number of files (excluding directories

    file_count = sum(1 for file_name in files if os.path.isfile(os.path.join('../deployed_apps_logs', file_name)))
    port = 5001 + file_count


    #STEP 4 : Create an nginx string with variables {port} {subdomain} concatenated and add to an ngix-config file.

    nginx_config = f"""
        server {{   
            server_name {subdomain}.techcamp.app;

            # ACME Challenge for SSL
            location /.well-known/acme-challenge/ {{
                root /var/www/paas/deployed_apps/{subdomain};
                default_type "text/plain";
                allow all;
            }}

            # Redirect all traffic to HTTPS
            location / {{
                return 301 https://$host$request_uri;
            }}
        }}

        # HTTPS Block
        server {{
            listen 443 ssl http2;
            server_name {subdomain}.techcamp.app;

            # SSL Certificates
            ssl_certificate /root/.acme.sh/{subdomain}.techcamp.app_ecc/fullchain.cer;
            ssl_certificate_key /root/.acme.sh/{subdomain}.techcamp.app_ecc/{subdomain}.techcamp.app.key;

            # Strong SSL Settings
            ssl_protocols TLSv1.2 TLSv1.3;
            ssl_prefer_server_ciphers on;
            ssl_ciphers HIGH:!aNULL:!MD5;

            # Reverse Proxy to Container
            location / {{
                proxy_pass http://{ip_address}:{port}; # Container running on port {port}
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }}

            # Logging (optional)
            access_log /var/www/paas/logs/{subdomain}/nginx_access.log;
            error_log /var/www/paas/logs/{subdomain}/nginx_error.log;
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

    print("Step 4: NGINX Server File Created Successfully-----------------")

    #STEP 5: Add deployed apps to db
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

    #STEP 6: Add Subdomain to DNS DigitalOcean
    digital_ocean_create_subdomain(subdomain)

    try:
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 6, "message" : "A record added for '+subdomain +'.techcamp.app to DigitalOcean DNS"}')
    except OSError as e:
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 6, "message" : "Error adding subdomain for '+subdomain +'.techcamp.app to DigitalOcean DNS"}')

    #Close Log file and RETURN BACK TO ROUTE
    with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(']')

    # os.chdir('..')

    try:
    # Ensure the folder exists before setting permissions
        # folder_path = "../success-report"
        # os.makedirs(folder_path, exist_ok=True)
        # os.chmod(folder_path, 0o755)
        # os.chdir(folder_path)

        # Create the success report file
        dockerfile_dir=f"/var/www/paas/deployed_apps/{subdomain}"

        success_file = os.path.join("../success-report", subdomain +".sh")
        with open(success_file, "a") as file:
            file.write(f"""
                       docker build -t {subdomain} {dockerfile_dir} && docker run -d -p {port}:80 --name {subdomain}-app {subdomain} 
                       """)

        print(f"Step 6: Success report created: {success_file}")

    except OSError as e:
        print(f"Step 6: Error creating success report for {subdomain}: {e}")

        
    return True

def destroy_application(subdomain):
    try:
        cur_path = "/app/destroy-report"
        os.chdir(cur_path)

        delete_subdomain_and_apps_by_name(subdomain)

        digital_ocean_delete_subdomain(subdomain)

        dest_file = os.path.join(cur_path, subdomain +".sh")

        if os.path.isfile(dest_file):  # Ensure it's a file
            os.remove(dest_file)
            print(f"STEP 5 : The pre existing destroy report has been removed.---------------------------------")

        destroy_file = os.path.join(os.curdir, subdomain +".sh")
        with open(destroy_file, "w") as file:
            file.write(f"""
                       destroy {subdomain} initiated at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                       """)

        print(f"Destroy report created: {destroy_file}")

    except OSError as e:
        print(f"Error creating destroy file for {subdomain}: {e}")

    return True

def rebuild_application(subdomain):
    try:
        # 1. Removing git folder
        cur_path="/app/deployed_apps"
        os.chdir(cur_path)

        app_dir = os.path.join(cur_path, subdomain)

        if os.path.exists(app_dir):
            try:
                # Using subprocess to remove the folder
                subprocess.run(['rm', '-rf', app_dir], check=True)
                print(f"STEP 1 : Successfully removed {app_dir} -------------------------------------------------")
            except subprocess.CalledProcessError as e:
                print(f"STEP 1 : Error occurred while removing {app_dir}: {e} ---------------------------------")
        else:
            print(f"STEP 1 : Directory {app_dir} does not exist.------------------------------------------------")

        # 2. Fetching the github url and port from DB
        result = session.query(DeployedApplication.github_url, DeployedApplication.port).join(Subdomain).filter(Subdomain.name == subdomain.strip().lower()).first()
        print("STEP 2 : Get Github URL and Port From DB result ---------------------------",  result)

        github_url, port = result
        print("STEP 2 : Github URL and Port---------------------------",  github_url, port)

        # 3. Cloning latest Github URL
        cur_path="/app/deployed_apps"
        os.chdir(cur_path)
        clone_path = os.path.join(subdomain)

        git_url_for_subdomain= f"git clone --depth 1 {github_url} {clone_path} "

        if subprocess.run(git_url_for_subdomain, shell=True).returncode == 0:
            print(f"STEP 3 : Re-deployment Successfully cloned {github_url} to {subdomain}---------------")
        else:
            print(f"STEP 3 : Error cloning {github_url} to {subdomain}---------------")

        # 4. Remove .git folder
        try:
            def change_permissions(file_path, mode):
                os.chmod(file_path, mode)
            mode = 0o777
            git_folder_path = os.path.join(clone_path, '.git')

            change_permissions(git_folder_path, mode)
            
            # os.chmod(git_folder_path, 0o777) 
            
            if os.path.exists(git_folder_path):
                shutil.rmtree(git_folder_path)
                print(f"STEP 4 : The .git folder in {clone_path} has been removed.---------------------------------")
            else:
                print(f"STEP 4 : The .git folder in {clone_path} does not exist.------------------------------------")
        except Exception as e:
            print("Redeploy App Error delete .git folder-------------", e)


        #STEP 5 to Copy Dockerfile to deployed apps
        try:
            html_files = f"cp /app/html_apps_requirements/Dockerfile /app/deployed_apps/{subdomain}"
            flask_files = f"cp /app/flask_apps_requirements/Dockerfile /app/deployed_apps/{subdomain}"

            # Execute the command
            subprocess.run(flask_files, check=True, shell=True)
            print(f"STEP 5 : Docker File copied successfully to {subdomain}.-------------------")
        except subprocess.CalledProcessError as e:
            print(f"STEP 5 : Error executing command: {e}----------------------------------------")
    

        # 6. Creating sh file to run the container
        rep_path = "/app/rebuild-report"
        os.chdir(rep_path)

        rebuild_file = os.path.join(rep_path , "re_"+subdomain +".sh")

        if os.path.isfile(rebuild_file):  
            os.remove(rebuild_file)
            
        print(f"STEP 6 : The pre existing rebuild report has been removed.---------------------------------")
        dockerfile_dir=f"/var/www/paas/deployed_apps/{subdomain}"

        with open(rebuild_file, "w") as file:
            file.write(f"""
                       docker build -t {subdomain} {dockerfile_dir} && docker run -d -p {port}:80 --name {subdomain}-app {subdomain} 
                       """)

        print(f"STEP 7 : Re-build report file created: {rebuild_file}")

    except OSError as e:
        print(f"STEP 7 : Error creating rebuild file for {subdomain}: {e}")

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