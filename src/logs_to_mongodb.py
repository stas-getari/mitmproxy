from db import logs
from utils import initialize_client_info, process_request_response, process_websocket, save_file

from mitmproxy import http


async def running():
    """Called when mitmproxy is fully started"""
    await initialize_client_info()


async def response(flow: http.HTTPFlow) -> None:
    """log all traffic to mongodb"""
    log_entry = process_request_response(flow)
    # log_entry = save_file(flow, log_entry)

    await logs.insert_one(log_entry)


async def websocket_message(flow: http.HTTPFlow) -> None:
    """Log all WebSocket messages to MongoDB"""
    try:
        if flow.websocket:
            log_entry = process_websocket(flow)

            await logs.update_one({"id": flow.id}, {"$set": log_entry}, upsert=True)
    except Exception as e:
        print(e)
