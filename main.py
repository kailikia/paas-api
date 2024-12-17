from flask import Flask, request, jsonify 
from flask_cors import CORS
import concurrent.futures
from config.services import *
import json
from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)
CORS(app)

CORS(app, resources={r"*": {"origins": "http://167.71.54.75:4000"}})

load_dotenv(find_dotenv())

@app.route('/')
def hello():
    print("-----------", digital_ocean_list_domains())
    return jsonify({"name":"Software Deployment Paas"}),200

@app.route('/sub-domains')
def sub_domain(): 
    #From DB
    subdomains = session.query(Subdomain).all()
    result = [{"name" : s.name, "id" : s.id, "user" :s.user} for s in subdomains]

    #From DO

    return jsonify(result)

@app.route('/sub-domain-availability', methods=["POST"])
def subdomain(): 
    subdomain_param = request.json["subdomain"].strip().lower()
    subdomain = session.query(Subdomain).filter(Subdomain.name==subdomain_param).count()

    if subdomain != 0 or len(subdomain_param) == 0:
        return jsonify({"subdomain":"not-available"})
    else:
        return jsonify({"subdomain":"available"}),200

@app.route('/deploy-html-app', methods=["POST", "GET"])
def deploy_app(): 
    if  request.method == "POST":
        try:
            subdomain = request.json["subdomain"].strip().lower()
            github_url=request.json["github_url"].strip().lower()
            user = "test"

            # Start SSH or Powershell Script to deploy app
            deploy_html_by_ssh_subprocess(github_url, subdomain, user) 

            # Call DO API to create subdomain and attach to subdomain and add A record
            # do_response = digital_ocean_create_subdomain(subdomain) 

            return jsonify({"message":"sub domain added and app deployed succcessfully","status": 1}),200
        except Exception as e:
            return jsonify({"message":e, "status": 1})


@app.route('/deploy-progress', methods=["POST"])
def deploy_progress(): 
    if  request.method == "POST":
        try:
            subdomain = request.json["subdomain"].strip().lower()
            deploy_subdomain_logs = "deployed_apps_logs/" + subdomain+".json"
            res =""
            with open(deploy_subdomain_logs, "r") as myfile:
                res = myfile.read()
            return json.loads(res)
        except:
            return '_'
    
if __name__=='__main__':
    app.run()