import os
from config.python_digitalocean import digitalocean
from config.models import Subdomain, create_engine, Base, sessionmaker
import subprocess, sys 

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

    #1. Write the deployment in a txt file with the name deploy_subdomain.txt. Echo a final text in the end to check IF statement

    #2. Create a new route that is reading that txt file

    #3. Check the route every 5 secs, check if error_in_step has changed to stop. Check in frontend to show progress in deploy_steps variable above

    #Change directory
    os.chdir('deployed_apps')

    #check size of file uloaded. If 
    git_subdomain= 'git clone https://github.com/kailikia/paas-app.git' + " "+ subdomain
    deploy_subdomain_logs = "../deployed_apps_logs/" + subdomain+".txt"

    #Delete existing log contents
    open(deploy_subdomain_logs, 'w').close()

    #initiate empty list in logs
    with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('[')

    #STEP 1: change directory to deployed_apps for subdomain
    if os.path.isdir(subdomain):
        #Delete existing subdomain project 
        os.system('rmdir /S /Q "{}"'.format(subdomain))
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('{"step" : 1, "message" : "Subdomain Domain Created for ' + subdomain+'"}')
    else:
        #Clone project    
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write('{"step" : 1, "message" : "Subdomain Domain Re-Created for '+ subdomain +'"}')

    #STEP 2: Clone into sundomain directory
    if subprocess.run(git_subdomain, shell=True).returncode == 0:
        #Edit txt to : Project cloned successfully 
        with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(',{"step" : 2, "message" : "Project '+subdomain +' cloned successfully"}')

    else:
        myfile.write(',{"step" : 2, "message" : "Error cloning project '+subdomain +'."}')

    #step 3: copy nginx-subdomain.config, sudomain_db.py, Dockerfile, and docker-compose files into the diretory.

       #step 3.2: build docker file with sudbomain name

        #step 3.3: run container using docker image created using subdomain

    #Close Log file and RETURN BACK TO ROUTE
    with open(deploy_subdomain_logs, "a") as myfile:
            myfile.write(']')
    os.chdir('..')

    return True