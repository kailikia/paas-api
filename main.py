from flask import Flask, request, jsonify 
from flask_cors import CORS
import concurrent.futures
from config.services import *
import json
from dotenv import load_dotenv, find_dotenv


app = Flask(__name__)
CORS(app)

load_dotenv(find_dotenv())


@app.route('/')
def hello():
    return jsonify({"name":"Software Deployment Paas"}),200

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
    if  request.method == "POST":
        try:
            subdomain = request.json["subdomain"].strip().lower()
            github_url=request.json["github_url"].strip().lower()
            db_name = request.json["db_name"]
            db_user = request.json["db_user"]
            db_password = request.json["db_password"]
            user = "test"

            #1. Start SSH or Powershell Script to deploy app
            ssh_deploy = deploy_ssh_subprocess(github_url, subdomain)
                
            #2. Save subdomain in DB
            session.add(add_subdomain(subdomain,user))
            session.commit()

            #3. Call DO API to create subdomain and attach to subdomain and add A record as expected
            # do_response = digital_ocean_create_subdomain(subdomain) 

            return jsonify({"message":"sub domain added and app deployed succcessfully","status": 1}),200
        except Exception as e:
            return jsonify({"message":e, "status": 1})


@app.route('/deploy-progress', methods=["POST"])
def deploy_progress(): 
    if  request.method == "POST":
        try:
            subdomain = request.json["subdomain"].strip().lower()
            deploy_subdomain_logs = "deployed_apps_logs/" + subdomain+".txt"
            res =""
            with open(deploy_subdomain_logs, "r") as myfile:
                res = myfile.read()
            return json.loads(res)
        except:
            return '_'
    
if __name__=='__main__':
    app.run()