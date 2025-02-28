from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import  sessionmaker, session

Base = declarative_base()

class Subdomain(Base):
    __tablename__ = "subdomains"
    id = Column("id", Integer, primary_key=True)
    name = Column("subdomain", String(100))
    user = Column("user", Integer)

    def __init__(self, name, user):
        self.name = name
        self.user = user

class DeployedApplication(Base):
    __tablename__ = "deployed_apps"
    id = Column("id", Integer, primary_key=True)
    subdomain_id =  Column(Integer, ForeignKey('subdomains.id'))
    github_url = Column("github_url", String(100))
    port = Column("port", Integer)
    app_type = Column(String(100))

    def __init__(self, subdomain_id, github_url, port, app_type):
        self.subdomain_id = subdomain_id
        self.github_url = github_url
        self.port = port
        self.app_type = app_type

class DeployedDatabase(Base):
    __tablename__ = "deployed_databases"
    id = Column("id", Integer, primary_key=True)
    deployed_app_id =  Column(Integer, ForeignKey('deployed_apps.id'))
    db_name = Column("db_name", String(100))
    db_user = Column("db_user", String(100))
    db_password = Column("db_password", String(100))

    def __init__(self, db_name, port):
        self.db_name = db_name
        self.port = port