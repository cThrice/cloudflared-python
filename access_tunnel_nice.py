# Adding args for header and chunk size, and integrating them into the code
# The header will be used for setting the WebSocket header and the chunk size for controlling the TCP read size.

import logging
import asyncio
import websockets
import argparse
import signal

# Initialize logging
logger = logging.getLogger("cloudflared_access_tunnel")

async def shutdown(signal, loop):
    """Cleanup tasks tied to the service's shutdown."""
    logger.info(f"Received exit signal {signal.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    [task.cancel() for task in tasks]

    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

# CLI setup
def setup_cli():
    parser = argparse.ArgumentParser(description='Python-based Cloudflared replacement.')
    parser.add_argument('--hostname', type=str, help='Cloudflare hostname', default="tcp.site.com")
    parser.add_argument('--url', type=str, help='Local URL to proxy', default="localhost:9210")
    parser.add_argument('--header', type=str, help='WebSocket header', default="")
    parser.add_argument('--chunk', type=int, help='TCP read chunk size', default=100)
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=logging_level)

    logger.info(f"CLI setup complete. Hostname: {args.hostname}, URL: {args.url}, Header: {args.header}, Chunk: {args.chunk}, Debug: {args.debug}")
    return args

async def send_to_cloudflare(reader, websocket, chunk_size):
    try:
        while True:
            if reader.at_eof():
                logger.info("TCP client has disconnected.")
                await websocket.close()
                break
            data = await reader.read(chunk_size)
            await websocket.send(data)
            logger.debug(f"Sent data to Cloudflare.")
    except Exception as e:
        logger.error(f"Exception while sending data to Cloudflare: {e}")
        await websocket.close()

async def receive_from_cloudflare(writer, websocket):
    try:
        while True:
            response = await websocket.recv()
            writer.write(response)
            await writer.drain()
            logger.debug(f"Received data from Cloudflare and sent to TCP client.")
    except websockets.ConnectionClosed as e:
        logger.info("WebSocket connection closed normally.")
    except Exception as e:
        logger.error(f"Exception while receiving data from Cloudflare: {e}")
    finally:
        writer.close()

async def handle_local_proxy(reader, writer, chunk_size):
    initial_data = await reader.read(chunk_size)
    headers = {}
    if args.header:
        key, value = args.header.split(":")
        headers[key.strip()] = value.strip()
    async with websockets.connect(f"ws://{args.hostname}", extra_headers=headers) as websocket:
        logger.info(f"Connected to Cloudflare: {args.hostname}")

        await websocket.send(initial_data)
        logger.debug("Initial data sent to Cloudflare.")

        # Create tasks for sending and receiving data
        send_task = asyncio.ensure_future(send_to_cloudflare(reader, websocket, chunk_size))
        recv_task = asyncio.ensure_future(receive_from_cloudflare(writer, websocket))

        # Wait for tasks to complete (they won't unless the connection is broken)
        await asyncio.gather(send_task, recv_task)

def setup_server(loop):
    local_host, local_port = args.url.split(":")
    # Start local TCP proxy server
    local_server = asyncio.start_server(lambda r, w: handle_local_proxy(r, w, args.chunk), local_host, int(local_port))
    loop.run_until_complete(local_server)
    logger.info(f"Local TCP proxy server is listening on {args.url}")

def setup_shutdown_hooks(loop):
    # Setup graceful shutdown
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s, loop))
        )

def main():
    global args
    args = setup_cli()

    loop = asyncio.get_event_loop()

    setup_server(loop)
    setup_shutdown_hooks(loop)

    # Keep event loop running to listen for incoming connections
    loop.run_forever()

main()
