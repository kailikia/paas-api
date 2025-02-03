from flask import Flask, request, jsonify 
from flask_cors import CORS
import concurrent.futures
from config.models import DeployedApplication
from config.services import *
import json
from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)
CORS(app)

CORS(app, resources={r"*": {"origins": "*"}})

load_dotenv(find_dotenv())

@app.route('/')
def hello():
    # print("-----------", digital_ocean_list_domains())
    return jsonify({"name":"Software Deployment Paas"}),200

@app.route('/sub-domains')
def sub_domain(): 
    #From DB
    subdomains = session.query(Subdomain).all()
    result = [{"name" : s.name, "id" : s.id, "user" :s.user} for s in subdomains]

    #From DO

    return jsonify(result)

@app.route("/subdomain-logs/<subdomain>")
def subdomain_logs(subdomain):
    return get_subdomain_logs(subdomain)

@app.route("/logs/acme/<subdomain>")
def acme_logs(subdomain):
    return get_acme_logs(subdomain)


@app.route("/logs/nginx/<subdomain>")
def nginx_logs(subdomain):
    return get_nginx_logs(subdomain)

@app.route("/logs/docker/<subdomain>")
def docker_logs(subdomain):
    return get_docker_logs(subdomain)

# query from DB sub domain, github url, status
@app.route('/db-data')
def db_data():

    data = session.query(DeployedApplication).with_entities(DeployedApplication.id,Subdomain.name, DeployedApplication.github_url, DeployedApplication.port).join(Subdomain).all()
    
    res = [{"id":s.id, "name" : s.name, "github_url" :s.github_url, "port":s.port } for s in data]

    # print("DB Data------------------------",res)

    return jsonify(res)


@app.route('/sub-domain-availability', methods=["POST"])
def subdomain(): 
    subdomain_param = request.json["subdomain"].strip().lower()
    subdomain_db = session.query(Subdomain).filter(Subdomain.name==subdomain_param).first()

    if subdomain_db or len(subdomain_param) == 0:
        return jsonify({"subdomain":"not-available"})
    else:
        return jsonify({"subdomain":"available"}),200

@app.route('/deploy-app', methods=["POST", "GET"])
def deploy_app(): 
    if  request.method == "POST":
        try:
            subdomain = request.json["subdomain"].strip().lower()
            github_url=request.json["github_url"].strip().lower()
            user = "test"

            # Start SSH or Powershell Script to deploy app
            deploy_html_by_ssh_subprocess(github_url, subdomain, user) 

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
        except Exception as e:
            print("Deploy Progress Error for "+subdomain+"------------------------",e)
            # Log the exception (optional) and return an error response
            error_message = str(e)
            return jsonify({"message": f"An error occurred: {error_message}"}), 500
        
@app.route('/destroy-app/<subdomain>', methods=["POST", "GET"])
def destroy_app(subdomain): 
    try:
        # Start the script or function to destroy the application
        destroy_application(subdomain)
        
        return jsonify({
            "message": f"Destroy app and sub-domain process started for: {subdomain}",
            "status": 1
        }), 200
    except Exception as e:
        # Log the exception (optional) and return an error response
        error_message = str(e)
        return jsonify({
            "message": f"An error occurred: {error_message}",
            "status": 0
        }), 500
    
if __name__=='__main__':
    app.run()