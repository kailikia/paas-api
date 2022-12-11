from flask import Flask, request, jsonify 
from models import Subdomain, create_engine, Base, sessionmaker
import subprocess, sys 
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

engine = create_engine("sqlite:///paas.db", connect_args={'check_same_thread': False})
Base.metadata.create_all(bind=engine)

session = sessionmaker(bind=engine)
session = session()

def add_subdomain(name,user):
      add_domain = Subdomain(name, user)
      session.add(add_domain)
      session.commit()
      return jsonify("Domain Stored Successfuly"),201

def deploy_ssh_subprocess(github_url):
    #RUN POWERSHELL AS ADMIN "Set-ExecutionPolicy RemoteSigned"
    deploy_steps = [
        'git clone '+ github_url,,
        'cp Dockerfile'
        'cp docker-compose.yml'
        'docker build -t subdomain'
        'docker run -p 5001:80 -t subdomain'
        'cp /etc/sites-available/subdomain.techcamp.co.ke'
        'restart nginx',
        'run script to put lets-encrypt/autorenew'
    ]
    #1. Write the deployment in a txt file with the name deploy_subdomain.txt. Echo a final text in the

    #2. Create a new wroute that is reading that txt file

    #3. Check the route every 5 secs, check if for the final part to stop the loop.Print out the echos in frontend to show progress in deploy_steps variable above

    #4.Delete the txt command after success deployment

    p = subprocess.run(deploy_steps, capture_output=True, shell = True)
    print(p)
  
        

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
       res = deploy_ssh_subprocess(github_url)
      
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