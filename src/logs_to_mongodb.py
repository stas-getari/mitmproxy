import json
import hashlib

from mitmproxy import http
from bson import json_util
from db import logs
from utils import process_request_response, save_file, process_websocket


async def response(flow: http.HTTPFlow) -> None:
    """log all traffic to mongodb"""
    log_entry = process_request_response(flow)
    log_entry = save_file(flow, log_entry)

    await logs.insert_one(json.loads(json_util.dumps(log_entry)))


# async def websocket_message(flow: http.HTTPFlow) -> None:
#     """Log all WebSocket messages to MongoDB"""
#     if flow.websocket:
#         log_entry = process_websocket(flow)

#         await logs.update_one({"id": flow.id}, {"$set": log_entry}, upsert=True)
