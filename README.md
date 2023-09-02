# Cloudflared-Python

This project is a Python-based implementation of the Cloudflared project by Cloudflare. It aims to adapt the modular components from Cloudflared into Python and potentially treating them as libraries. Our broader goal is to create a Python substitute for Cloudflared, this currently includes scripts for establishing connections to Cloudflare and proxying arbitrary incoming TCP connections over WebSocket connection.

## Getting Started

Before you begin, you should have the following prerequisites installed:

Python 3.7 or higher
Websockets Python library
Cloudflared installed on the server side

You can install the necessary Python libraries with the following commands:
```
pip install websockets
```

To install Cloudflared, follow the instructions on the official [Cloudflared installation guide.](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/). 

## Using The Script

At present, access_tunnel.py is acting as the primary script. You can run this script using the following command:
```
python access_tunnel.py --hostname <YOUR_HOSTNAME> --url <LOCAL_URL_TO_PROXY>
```

Replace <YOUR_HOSTNAME> with your Cloudflare hostname and <LOCAL_URL_TO_PROXY> with the local URL you want to proxy. Example:
```
python access_tunnel.py --hostname tcp.site.com --url localhost:9210
```

By default, if no parameters are passed, the script assumes your Cloudflare hostname as tcp.site.com and the local URL as localhost:9210. The script is designed to be executed directly and does not require any special permissions or environment settings.

## Future Work and Contributions

We are in the process of introducing server_tunnel.py to enhance the versatility of this project. Future work includes secure authentication and robust error handling to increase the reliability and security of the script. Currently, this project is in the experimental phase, and should not be used in a production environment.

We welcome contributions to this open-source project. Whether you are reporting issues, suggesting new features or offering your own code changes through pull requests, your input is valuable to us.