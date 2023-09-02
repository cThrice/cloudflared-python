# Cloudflared-Python

This project is a Python-based implementation of the Cloudflared project by Cloudflare. It aims to adapt the modular components from Cloudflared into Python and potentially treating them as libraries. Our broader goal is to create a Python substitute for Cloudflared, this currently includes scripts for establishing connections to Cloudflare and proxying arbitrary incoming TCP connections over WebSocket connection.

At present, we have access_tunnel.py acting as the primary script.

You can run the script using the following command:

Bash
python access_tunnel.py --hostname <YOUR_HOSTNAME> --url <LOCAL_URL_TO_PROXY>


Replace <YOUR_HOSTNAME> with your Cloudflare hostname and <LOCAL_URL_TO_PROXY> with the local URL that you want to proxy. Example:

Bash
python access_tunnel.py --hostname tcp.site.com --url localhost:9210


Please note, the script assumes your Cloudflare hostname as tcp.site.com and the local URL as localhost:9210 by default if no parameters are passed. The script is designed to be executed directly and does not require any special permissions or environment settings. It does, however, require Python 3.7 or higher and the websockets and argparse libraries.

We are in the process of introducing server_tunnel.py to enhance the versatility of this project – name is derived from how Cloudflared seems to reference them.

Future Work includes secure authentication and robust error handling to increase the reliability and security of the script. As it stands, this project is in the experimental phase, and should not be used in a production environment.

Contributions are more than welcome as this is an open source project. Feel free to submit issues, feature requests and pull requests.