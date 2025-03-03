from datetime import datetime
import os
from config.models import DeployedApplication, Subdomain, create_engine, Base, sessionmaker
import subprocess, sys 
import digitalocean
import shutil, json, requests
from pydo import Client
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures


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

def add_deployed_apps(subdomain_id,github_url,port, choice):
      add_app = DeployedApplication(subdomain_id, github_url, port, choice)
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


#--------------------------------------------------------------------------------------------- Deploy and Server Functions 
def deploy_html_by_ssh_subprocess(github_url, subdomain, user, choice):
    cur_path = "/app/deployed_apps"
    os.chdir(cur_path)
    clone_path = os.path.join(subdomain)

    deploy_subdomain_logs = os.path.join("../deployed_apps_logs", subdomain + ".json")
    deploy_server_logs = os.path.join("../deployed_apps_logs", subdomain + "-server.json")

    # Initialize logs in memory
    log_entries = []

    server_file = {
        "subdomain": subdomain,
        "acme": "", "docker": "", "success-report": "",
        "nginx-files": "", "symlink": "", "postgres": "",
        "restart": "", "complete": False
    }

    # Write server logs at the start
    with open(deploy_server_logs, "w") as servfile:
        json.dump(server_file, servfile, indent=4)

    # Initialize concurrent tasks
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_tasks = {
            executor.submit(lambda: subprocess.run(f"git clone --depth 1 {github_url} {clone_path}", shell=True).returncode == 0): "clone_repo",
            executor.submit(lambda: (shutil.rmtree(os.path.join(subdomain, '.git')) if os.path.exists(os.path.join(subdomain, '.git')) else None, os.chmod(os.path.join(subdomain), 0o777))): "setup_permissions",
            executor.submit(lambda: subprocess.run(f"cp {'/app/html_apps_requirements/Dockerfile' if choice == 'html' else '/app/flask_apps_requirements/*'} /app/deployed_apps/{subdomain}", shell=True).returncode == 0): "copy_dockerfile",
            executor.submit(lambda: (open(f"../db-create/{subdomain}.sh", "w").write(f'sudo -u postgres PGPASSWORD="12345" psql -c "CREATE DATABASE {subdomain} OWNER postgres; GRANT ALL PRIVILEGES ON DATABASE {subdomain} TO postgres;"') if choice == 'flask' else None)): "create_database",
            executor.submit(lambda: open(f"../deployed_nginx_files/{subdomain}.techcamp.app", "w").write(f"""
                server {{   
                    server_name {subdomain}.techcamp.app;
                    location /.well-known/acme-challenge/ {{
                        root /var/www/paas/deployed_apps/{subdomain};
                        allow all;
                    }}
                    location / {{ return 301 https://$host$request_uri; }}
                }}

                server {{
                    listen 443 ssl http2;
                    server_name {subdomain}.techcamp.app;
                    ssl_certificate /root/.acme.sh/{subdomain}.techcamp.app_ecc/fullchain.cer;
                    ssl_certificate_key /root/.acme.sh/{subdomain}.techcamp.app_ecc/{subdomain}.techcamp.app.key;
                    ssl_protocols TLSv1.2 TLSv1.3;
                    ssl_ciphers HIGH:!aNULL:!MD5;
                    location / {{
                        proxy_pass http://127.0.0.1:5000;
                    }}
                }}
            """)): "configure_nginx"
        }

        logs = [
            {"task": future_tasks[future], "status": "success", "result": result}
            if not isinstance(result := future.result(), Exception)
            else {"task": future_tasks[future], "status": "failed", "error": str(result)}
            for future in concurrent.futures.as_completed(future_tasks)
        ]

        # Process all futures using list comprehension
        log_entries.extend(logs)

    # Write log once at the end
    with open(deploy_subdomain_logs, "w") as myfile:
        json.dump(log_entries, myfile, indent=4)

    return True


#--------------------------------------------------------------------------------------------- Destroy the application
def remove_destroy_report(dest_file):
    """Removes an existing destroy report file if it exists."""
    if os.path.isfile(dest_file):
        os.remove(dest_file)

def create_destroy_report(destroy_file, subdomain):
    """Creates a new destroy report file."""
    with open(destroy_file, "w") as file:
        file.write(f"destroy {subdomain} initiated at {datetime.now():%Y-%m-%d %H:%M:%S}\n")

def destroy_application(subdomain):
    try:
        cur_path = "/app/destroy-report"
        os.chdir(cur_path)

        # Run tasks concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_tasks = {
                executor.submit(delete_subdomain_and_apps_by_name, subdomain): "delete_subdomain",
                executor.submit(digital_ocean_delete_subdomain, subdomain): "delete_dns",
                executor.submit(remove_destroy_report, os.path.join(cur_path, f"{subdomain}.sh")): "remove_report",
            }

            for future in concurrent.futures.as_completed(future_tasks):
                future.result()  # Handle exceptions if necessary

        # Create a new destroy report after cleanup
        create_destroy_report(os.path.join(cur_path, f"{subdomain}.sh"), subdomain)

    except OSError:
        pass  # Optionally log the error

    return True

#---------------------------------------------------------------------------------------------- Rebuild the applica
def remove_directory(path):
    """Removes a directory using subprocess."""
    if os.path.exists(path):
        try:
            subprocess.run(['rm', '-rf', path], check=True)
            return f"Removed {path}"
        except subprocess.CalledProcessError as e:
            return f"Error removing {path}: {e}"
    return f"Directory {path} does not exist"

def fetch_github_url_and_port(subdomain):
    """Fetches GitHub URL and port from DB."""
    result = (
        session.query(DeployedApplication.github_url, DeployedApplication.port)
        .join(Subdomain)
        .filter(Subdomain.name == subdomain.strip().lower())
        .first()
    )
    return result if result else (None, None)

def clone_repository(github_url, clone_path):
    """Clones a GitHub repository."""
    command = f"git clone --depth 1 {github_url} {clone_path}"
    return f"Cloned {github_url} to {clone_path}" if subprocess.run(command, shell=True).returncode == 0 else f"Error cloning {github_url}"

def remove_git_folder(path):
    """Removes the .git folder."""
    git_folder = os.path.join(path, ".git")
    if os.path.exists(git_folder):
        shutil.rmtree(git_folder)
        return f"Removed .git folder in {path}"
    return f".git folder in {path} does not exist"

def copy_dockerfile(subdomain, app_type):
    """Copies Dockerfile based on app type."""
    source = "/app/flask_apps_requirements/*" if app_type == "flask" else "/app/html_apps_requirements/Dockerfile"
    command = f"cp {source} /app/deployed_apps/{subdomain}"
    return f"Dockerfile copied to {subdomain}" if subprocess.run(command, check=True, shell=True) else f"Error copying Dockerfile to {subdomain}"

def create_rebuild_script(subdomain, port):
    """Creates a rebuild script."""
    rep_path = "/app/rebuild-report"
    os.chdir(rep_path)
    
    rebuild_file = os.path.join(rep_path, f"re_{subdomain}.sh")
    if os.path.isfile(rebuild_file):
        os.remove(rebuild_file)

    dockerfile_dir = f"/var/www/paas/deployed_apps/{subdomain}"
    with open(rebuild_file, "w") as file:
        file.write(f"docker build -t {subdomain} {dockerfile_dir} && docker run -d -p {port}:80 --name {subdomain}-app {subdomain}")
    
    return f"Rebuild report created: {rebuild_file}"

def rebuild_application(subdomain):
    logs = []
    
    try:
        os.chdir("/app/deployed_apps")
        app_dir = os.path.join("/app/deployed_apps", subdomain)

        # Parallel execution of independent tasks
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_tasks = {
                executor.submit(remove_directory, app_dir): "remove_directory",
                executor.submit(fetch_github_url_and_port, subdomain): "fetch_github_url_and_port"
            }
            
            for future in concurrent.futures.as_completed(future_tasks):
                result = future.result()
                if isinstance(result, tuple):  # DB result (github_url, port)
                    github_url, port = result
                else:
                    logs.append(result)

        if not github_url or not port:
            return f"Error: No GitHub URL or port found for {subdomain}"

        clone_path = os.path.join("/app/deployed_apps", subdomain)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_tasks = {
                executor.submit(clone_repository, github_url, clone_path): "clone_repository",
                executor.submit(remove_git_folder, clone_path): "remove_git_folder",
            }

            for future in concurrent.futures.as_completed(future_tasks):
                logs.append(future.result())

        # Copy the correct Dockerfile
        app_type = (
            session.query(DeployedApplication.app_type)
            .join(Subdomain)
            .filter(Subdomain.name == subdomain.strip().lower())
            .first()
        )

        if app_type:
            logs.append(copy_dockerfile(subdomain, app_type[0]))

        logs.append(create_rebuild_script(subdomain, port))

    except OSError as e:
        logs.append(f"Error: {e}")

    return logs
