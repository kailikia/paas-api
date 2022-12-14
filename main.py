from flask import Flask, request, jsonify 
from api_files.models import Subdomain, create_engine, Base, sessionmaker
import subprocess, sys 
from flask_cors import CORS
from python_digitalocean import digitalocean
import os

app = Flask(__name__)
CORS(app)

engine = create_engine("sqlite:///api_files/paas.db", connect_args={'check_same_thread': False})
Base.metadata.create_all(bind=engine)

session = sessionmaker(bind=engine)
session = session()

TOKEN="dop_v1_02aa3f24caa7c665d082dad0bfa9fc67f79652a917f230eb99c50342da459024"
domain = digitalocean.Domain(token=TOKEN, name="techcamp.app")
records = domain.get_records()
for r in records:
    print(r.type, r.data)

manager = digitalocean.Manager(token=TOKEN)
my_projects = manager.get_all_projects()
resources = my_projects[0].get_all_resources()
print(resources)

def add_subdomain(name,user):
      add_domain = Subdomain(name, user)
      session.add(add_domain)
      session.commit()
      return jsonify("Domain Stored Successfuly"),201

def deploy_ssh_subprocess(github_url, subdomain):
    error_in_step = 0
    #In windows RUN POWERSHELL AS ADMIN and run command "Set-ExecutionPolicy RemoteSigned"

    #1. Write the deployment in a txt file with the name deploy_subdomain.txt. Echo a final text in the end to check IF statement

    #2. Create a new route that is reading that txt file

    #3. Check the route every 5 secs, check if error_in_step has changed to stop. Check in frontend to show progress in deploy_steps variable above

    os.chdir('deployed_apps')
    clone_git_subdomain= 'git clone https://github.com/kailikia/paas-app.git' + " "+ subdomain
    print(clone_git_subdomain)

    #step 1: change directory to deployed_apps for subdomain
    if os.path.isdir(subdomain):
        os.system('rmdir /S /Q "{}"'.format(subdomain))
        print("Deployment 1: -----", "Deleted time deployment for subdomain")

    else:
         #Edit txt to : Project cloned successfully 
        print("Deployment 1: -----", "First time deployment for subdomain")

    #step 2: Clone into sundomain directory
    if subprocess.run(clone_git_subdomain, shell=True).returncode == 0:
        #Edit txt to : Project cloned successfully 
        print("Deployment 2: -----","Project cloned successfully")
    else:
        print("Deployment 2: -----", "Error in accessing Git Repository ")

    #step 3: copy nginx, Dockerfile, and docker-compose files into the diretory.

       #step 3.2: build docker file with sudbomain name

        #step 3.3: run container using docker image created using subdomain

    #RETURN BACK TO ROUTE
    os.chdir('..')


@app.route('/')
def hello():
    return jsonify({"name":"Software Deployment Paas"}),200

@app.route('/sub-domain-availability', methods=["POST"])
def subdomain(): 
    subdomain_param = request.json["subdomain"].strip().lower()
    subdomain = session.query(Subdomain).filter(Subdomain.name==subdomain_param).count()

    if subdomain != 0 or len(subdomain_param) == 0:
        return jsonify({"subdomain":"not-available"})
    else:
        return jsonify({"subdomain":"available"}),200

@app.route('/deploy-app', methods=["POST", "GET"])
def deploy_app(): 
    print("Request method", request)
    if  request.method == "POST":
       subdomain = request.json["subdomain"].strip().lower()
       github_url="https.github.com/"+ request.json["github_url"].strip().lower()
       db_name = request.json["db_name"]
       db_user = request.json["db_user"]
       db_password = request.json["db_password"]
       user = "test"

       #1. Save subdomain in DB
       #add_subdomain(subdomain,user)

       #2. Call DO API to create subdomain and attach to subdomain and add A record as expected

       #2. Start SSH or Powershell Script to deploy app
       res = deploy_ssh_subprocess(github_url, subdomain)
      
       #3. Create db 

       return jsonify({"message":"sub domain added succcessfully"}),200
    else:
        return jsonify({"message":"invalid"})


@app.route('/sub-domains')
def sub_domains(): 
    subdomains = session.query(Subdomain).all()
    result = []
    for s in subdomains:
        row={}
        row["name"]=s.name
        row["id"]=s.id
        row["user"]=s.user
        result.append(row)
    return jsonify(result)

    
if __name__=='__main__':
    app.run()