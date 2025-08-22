# Here we create MongoDB client to interact with it's collections

import asyncio
from os import environ as env

import motor.motor_asyncio

# env
username = env.get("MONGO_INITDB_ROOT_USERNAME")
password = env.get("MONGO_INITDB_ROOT_PASSWORD")
mongo_host = env.get("MONGO_HOST")
port = env.get("MONGO_INITDB_PORT")

# get DB and collections
host = f"mongodb://{username}:{password}@{mongo_host}:{port}/?authSource=admin"
client = motor.motor_asyncio.AsyncIOMotorClient(host)
client.get_io_loop = asyncio.get_running_loop  # that line is very important to prevent event_loop error

logs = client["test"]["requestInterceptions"]
clients = client["test"]["clients"]
