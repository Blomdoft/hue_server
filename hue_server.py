from http.server import BaseHTTPRequestHandler, HTTPServer
from phue import Bridge
import json
import os

# Replace with the IP address of your Philips Hue bridge
BRIDGE_IP = '192.168.1.2'
# The port where the HTTP server will listen
SERVER_PORT = 8080
# Path to the configuration directory
CONFIG_DIR = '/app/config'
USERNAME_FILE = os.path.join(CONFIG_DIR, 'hue_username.txt')

# Function to register the bridge and save the username
def register_bridge():
    bridge = Bridge(BRIDGE_IP)
    try:
        bridge.connect()
        username = bridge.username
        with open(USERNAME_FILE, 'w') as file:
            file.write(username)
        return {'status': 'success', 'username': username}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# Load the saved username from the file if it exists
if os.path.exists(USERNAME_FILE):
    with open(USERNAME_FILE, 'r') as file:
        HUE_USERNAME = file.read().strip()
    bridge = Bridge(BRIDGE_IP, username=HUE_USERNAME)
else:
    bridge = None

class HueHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/list_outlets':
            self.list_outlets()
        elif self.path.startswith('/set_outlet_state'):
            self.set_outlet_state()
        elif self.path == '/register':
            self.register()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def list_outlets(self):
        if not bridge:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Bridge not registered')
            return
        
        outlets = [
            {
                'name': light.name,
                'state': light.on
            } for light in bridge.lights if light.type == 'On/Off plug-in unit'
        ]
        
        response = {
            'status': 'success',
            'outlets': outlets
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def set_outlet_state(self):
        if not bridge:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Bridge not registered')
            return

        query_components = self.parse_query_params()
        outlet_name = query_components.get('name')
        state = query_components.get('state')

        if outlet_name is None or state is None:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Bad Request: name and state parameters are required')
            return

        state = state.lower() in ['true', '1', 'on']

        outlets = [light for light in bridge.lights if light.type == 'On/Off plug-in unit' and light.name == outlet_name]
        
        if not outlets:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Outlet not found')
            return

        outlet = outlets[0]
        outlet.on = state
        
        response = {
            'status': 'success',
            'outlet': outlet.name,
            'new_state': outlet.on
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def register(self):
        response = register_bridge()
        if response['status'] == 'success':
            global bridge
            bridge = Bridge(BRIDGE_IP, username=response['username'])
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def parse_query_params(self):
        from urllib.parse import parse_qs, urlparse
        query = urlparse(self.path).query
        return {k: v[0] for k, v in parse_qs(query).items()}

def run(server_class=HTTPServer, handler_class=HueHandler, port=SERVER_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()

