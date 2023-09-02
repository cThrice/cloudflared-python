# Final Proof-of-Concept (PoC) Python Script for Cloudflared Replacement
# This version connects to Cloudflare via WebSocket AFTER an inbound TCP connection is established.
# It then proxies arbitrary incoming TCP connections over to the WebSocket connection.

import logging
import asyncio
import websockets
import argparse

# Initialize logging
logger = logging.getLogger("cloudflared_access_tunnel")

# CLI setup (Relevant Go Code: cmd.go)
def setup_cli():
    parser = argparse.ArgumentParser(description='Python-based Cloudflared replacement.')
    parser.add_argument('--hostname', type=str, help='Cloudflare hostname', default="tcp.site.com")
    parser.add_argument('--url', type=str, help='Local URL to proxy', default="localhost:9210")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--header', type=str, help='Header to be passed with the initial WebSocket connection', default=None)
    args = parser.parse_args()

    # Configure logging
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=logging_level)

    logger.info(f"CLI setup complete. Hostname: {args.hostname}, URL: {args.url}, Debug: {args.debug}")
    return args

# Coroutine to send data to Cloudflare (Relevant Go Code: connection.go)
async def send_to_cloudflare(reader, websocket):
    while True:
        data = await reader.read(100)
        if not data:
            logger.info("TCP client has disconnected.")
            break
        await websocket.send(data)
        logger.debug(f"Sent data to Cloudflare.")

# Coroutine to receive data from Cloudflare and send to TCP client (Relevant Go Code: connection.go)
async def receive_from_cloudflare(writer, websocket):
    while True:
        response = await websocket.recv()
        writer.write(response)
        await writer.drain()
        logger.debug(f"Received data from Cloudflare and sent to TCP client.")

# Handle incoming TCP connections and forward to Cloudflare (Relevant Go Code: connection.go and websocket.go)
async def handle_local_proxy(reader, writer):
    logger.info("Handling incoming TCP connection...")
    peername = writer.get_extra_info('peername')
    
    # Read initial data for Cloudflare WebSocket connection
    initial_data = await reader.read(100)

    # Extra headers if any
    extra_headers = {}
    if args.header:
        key, value = args.header.split(":")
        extra_headers[key.strip()] = value.strip()
    
    # Connect to Cloudflare using WebSocket and initial data
    async with websockets.connect(f"ws://{args.hostname}", extra_headers=extra_headers) as websocket:
        logger.info(f"Connected to Cloudflare: {args.hostname}")
        
        await websocket.send(initial_data)
        logger.debug("Initial data sent to Cloudflare.")
        
        # Create tasks for sending and receiving data
        send_task = asyncio.create_task(send_to_cloudflare(reader, websocket))
        recv_task = asyncio.create_task(receive_from_cloudflare(writer, websocket))
        
        # Wait for tasks to complete (they won't unless the connection is broken)
        await asyncio.gather(send_task, recv_task)

# Main function to start local TCP proxy server (Relevant Go Code: cmd.go and server.go)
def main():
    global args  # Make args globally accessible
    logger.info("Starting main function...")
    args = setup_cli()
    
    loop = asyncio.get_event_loop()
    local_host, local_port = args.url.split(":")
    
    # Start local TCP proxy server
    local_server = asyncio.start_server(handle_local_proxy, local_host, int(local_port))
    loop.run_until_complete(local_server)
    logger.info(f"Local TCP proxy server is listening on {args.url}")

    # Keep event loop running to listen for incoming connections
    loop.run_forever()

# Uncomment the line below to run the main function
# main()

# Future work: Implement secure authentication and robust error handling