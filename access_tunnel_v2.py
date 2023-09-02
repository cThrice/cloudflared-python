# Modified Proof-of-Concept (PoC) Python Script for Cloudflared Replacement with Further Improvements

import logging
import asyncio
import websockets
import argparse
import signal

# Initialize logging
logger = logging.getLogger("cloudflared_access_tunnel")

# CLI setup (Relevant Go Code: cmd.go)
def setup_cli():
    parser = argparse.ArgumentParser(description='Python-based Cloudflared replacement.')
    parser.add_argument('--hostname', type=str, help='Cloudflare hostname', default="tcp.site.com")
    parser.add_argument('--url', type=str, help='Local URL to proxy', default="localhost:9210")
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--chunk-size', type=int, help='Data chunk size', default=100)
    args = parser.parse_args()

    # Configure logging
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=logging_level)

    logger.info(f"CLI setup complete. Hostname: {args.hostname}, URL: {args.url}, Debug: {args.debug}, Chunk Size: {args.chunk_size}")
    return args

# Coroutine to send data to Cloudflare (Relevant Go Code: connection.go)
async def send_to_cloudflare(reader, websocket):
    while True:
        data = await reader.read(args.chunk_size)
        if not data:
            logger.info("TCP client has disconnected.")
            break
        await websocket.send(data)
        logger.debug("Sent data to Cloudflare.")

# Coroutine to receive data from Cloudflare and send to TCP client (Relevant Go Code: connection.go)
async def receive_from_cloudflare(writer, websocket):
    while True:
        response = await websocket.recv()
        writer.write(response)
        await writer.drain()
        logger.debug("Received data from Cloudflare and sent to TCP client.")

# Handle incoming TCP connections and forward to Cloudflare (Relevant Go Code: connection.go and websocket.go)
async def handle_local_proxy(reader, writer):
    logger.info("Handling incoming TCP connection...")
    
    # Read initial data for Cloudflare WebSocket connection
    initial_data = await reader.read(args.chunk_size)
    
    # Connect to Cloudflare using WebSocket and initial data
    async with websockets.connect(f"ws://{args.hostname}") as websocket:
        logger.info(f"Connected to Cloudflare: {args.hostname}")
        
        await websocket.send(initial_data)
        logger.debug("Initial data sent to Cloudflare.")
        
        # Create tasks for sending and receiving data
        send_task = asyncio.ensure_future(send_to_cloudflare(reader, websocket))
        recv_task = asyncio.ensure_future(receive_from_cloudflare(writer, websocket))
        
        # Wait for tasks to complete (they won't unless the connection is broken)
        await asyncio.gather(send_task, recv_task)

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    logger.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]

    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

# Main function to start local TCP proxy server (Relevant Go Code: cmd.go and server.go)
def main():
    global args  # Make args globally accessible
    logger.info("Starting main function...")
    args = setup_cli()
    
    loop = asyncio.get_event_loop()
    local_host, local_port = args.url.split(":")
    
    # Setup graceful shutdown
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )
    
    # Start local TCP proxy server
    local_server = asyncio.start_server(handle_local_proxy, local_host, int(local_port))
    loop.run_until_complete(local_server)
    logger.info(f"Local TCP proxy server is listening on {args.url}")

    # Keep event loop running to listen for incoming connections
    loop.run_forever()

# Uncomment the line below to run the main function
main()

# Future work: Implement secure authentication and robust error handling

