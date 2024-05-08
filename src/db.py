import asyncio

import yaml
import motor.motor_asyncio


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# get DB and collections
host = f'mongodb://{config["username"]}:{config["password"]}@{config["mongo_host"]}:{config["port"]}/?authSource=admin'
client = motor.motor_asyncio.AsyncIOMotorClient(host)
client.get_io_loop = asyncio.get_running_loop  # that line is very important to prevent event_loop error
db = client["mitmproxy"]
logs = db["logs"]
