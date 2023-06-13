"""
aiohttp based client
"""

__version___ = "0.9"

import asyncio

from subs.network.http.client import HttpClient
from subs.network.settings import ServClientShared

class Client(ServClientShared):
    settings = {'name': 'client',
                }

    http_client = None

    def __init__(self) -> None:
        self.stop_flag = asyncio.Event()
        super().__init__()

    async def start(self):
        self.http_task = asyncio.create_task(self.setup_http_client())

        await self.setup_broadcast()
        self.broadcast.datagram_received = self.broadcast_received
        self.broadcast.error_received = self.broadcast_error_received
        self.broadcast.connection_lost = self.broadcast_connection_lost

        await self.http_task
        await self.stop_flag.wait()
    
    async def on_register(self, data, addr):
        """
        called when server announcement is received
        """
        server = f'https://{addr[0]}:{self.HTTP_PORT}'

        if server != self.http_client.server:
            print(f'server found @{addr[0]}')
            self.http_client.server = server        
    
    async def register_self(self):
        send_data = self.settings
        response_data = await self.http_client.post('register', 
                data=send_data)

        if (new_set := set(response_data.items()) - set(send_data.items())):
            self.settings.update(response_data)
            print(f'new settings: {new_set}')

    async def on_connect(self, response):
        if response.ok:
            print(f'Connected to : {response.host}')
            print(f"Connect: {await response.text()}")
            await self.register_self()
        else:
            print(f"Cannot Connect: Incorrect server response {response.status}")

    async def on_datagram(self, data, addr):
        print(f'Received from {addr}: {data}')

    async def setup_http_client(self):
        self.http_client = HttpClient()
        self.http_client.__dict__.update(self.http_paths)
        self.http_client.on_connect = self.on_connect
        self.http_client.on_ws_msg = self.on_ws_msg
        await self.http_client.aio_start()

    async def send_ws(self, data):
        """
        send data over websocket
        - data: data to send
        """
        return await self.http_client.websocket_write(data)

    async def on_ws_msg(self, origin, msg):
        if (isinstance(msg, dict) and 
            msg.get('type', '') == 'SVR_CMD'):
            f, ar, kw = (msg.get(k, alt) for 
                         k, alt in zip(('func', 'ar', 'kw'), 
                                       (None, [], {})))
            await getattr(self, f"on_cmd_{f}")(*ar, **kw)


        else:
            print(f'unhandled websocket message: {origin} - {msg}')
    
    async def send_data(self, data, **kwargs):
        await self.http_client.send_big_object(data, **kwargs)

    # COMMANDS send via websocket, must start with on_cmd_{cmd name}
    async def on_cmd_test(self, *args, **kwargs):
        print('test ', args, kwargs)
    
    async def on_cmd_send_file(self, filename):
        print('send_file', filename)


    def rename(self, name):
        self.settings['name'] = name

if __name__ == "__main__":
    import threading as tr
    c = Client()

    tr.Thread(target=asyncio.run, args=(c.start(), )).start()


