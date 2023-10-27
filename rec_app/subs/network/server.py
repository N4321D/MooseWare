"""
aiohttp based server
"""

__version___ = "0.9"

import asyncio
from aiohttp import web

from subs.network.http.server import HttpServer
from subs.network.settings import ServClientShared


class Server(ServClientShared):
    ANNOUCE_INTERVAL = 2            # interval to send annoucement messages

    clients = {}                    # dict with clients 
    client_lookup = {}              # dict with clientname: ip lookup

    def __init__(self) -> None:
        self.stop_flag = asyncio.Event()
        super().__init__()


    async def start(self):
        self.http_server_task = asyncio.create_task(self.setup_http_server())
        await self.setup_broadcast()
        self.annouce_task = asyncio.create_task(self._annouce_loop())
        await self.stop_flag.wait()

    async def setup_http_server(self):
        self.http_server = HttpServer()
        self.http_server.boundary = self.BOUNDARY
        self.http_server.PORT = self.HTTP_PORT
        self.http_server.on_post_cmd = self.on_post_cmd
        self.http_server.on_get_cmd = self.on_get_cmd
        self.http_server.on_ws_close = self.close_client
        self.http_server.on_ws_msg = self.on_ws_msg
        self.http_server.on_big_object = self.on_big_object
        self.http_server.__dict__.update(self.http_paths)
        await self.http_server.start()

    async def on_get_cmd(self, cmd, request):
        print(f"request from {request.remote} - {cmd}")
        return web.Response(text=f'CMD: {cmd} received')

    async def on_post_cmd(self, cmd, request, data):
        try: 
            _f = getattr(self, f'do_pcmd_{cmd}')
        
        except AttributeError:
            print(f"Unprocessed Post from {request.remote}: {cmd} - {request.content_type} - {str(data):.50s}")
            return web.HTTPBadRequest()

        out = await _f(request, data)
        return  out 

    async def on_big_object(self, request, data):
        print(f'result received from {request.origin}, size: {len(data)/1e6:.2f} MB'
              f"{request.headers}")

    async def stop(self):
        """
        stop & cleanup
        """
        self.annouce_task.cancel()
        await self.http_server.stop()
        try:
            asyncio.wait_for(self.http_server_task, timeout=3)

        except asyncio.TimeoutError:
            pass

    async def _annouce_loop(self):
        write_broadcast = self.write_broadcast
        try:
            while not await asyncio.sleep(1):
                await write_broadcast(self.SERVER_ANNOUNCE_MSG, encrypt=False)
                
        except asyncio.CancelledError:
            pass

    async def send_cmd(self, client, func, *args, **kwargs):
        """
        send server command to client
        - func: name of command (client.on_cmd_{name} is called)
        - args: args for command
        - kwargs: kwargs for command
        """
        await self.send_ws(client, {'type': 'SVR_CMD',
                                    'func': func,
                                     'ar': args,
                                     'kw': kwargs,})

    def send_data(self, *args, **kwargs):
        print(f"unhandled Server send data: {args}, {kwargs}")

    async def send_ws(self, client, data):
        """
        send data over websocket
        - client: name or ip address of client
        - data: data to send
        """
        ip = self.client_lookup.get(client, client)     # lookup client name if not found use ip
        
        if not (ws := self.http_server.ws.get(ip)):
            return
        
        return await ws.websocket_write(data)

    async def close_client(self, client):
        """
        clean up client on disconnect of websocket
        """
        name = self.clients[client]['name']
        del self.clients[client]
        del self.client_lookup[name]
        print(f"client {client} - '{name}' disconnected")
        self.on_client_disconnected()

    def on_client_disconnected(self):
        """
        called when client disconnects
        """
        ...
    
    async def on_ws_msg(self, origin, data):
        print(f'Server websocket msg received from {origin}: {data}')       

    # MISC 
    def rename(self, name='Setup'):
        """
        creates new client name if a client with the same name is
        already registered
        """
        if name not in self.client_lookup:
            return name

        if "." in name:
            *old_name, i = name.split('.')
            try:
                i = int(i)
            except ValueError:
                i = 0
            old_name = "".join(old_name)

        else:
            old_name, i = name, 0

        while name in self.client_lookup:
            if i >= 1000:
                raise RecursionError("Error: 1000 clients with the same name, "
                                     "stopped trying to create a new name")
            i += 1
            name = f"{old_name}.{i:03d}"

        return name

    # POST COMMANDS (NOTE: need to be named do_pcmd_{cmd name})      
    async def do_pcmd_register(self, request, data):
        """
        called when a new client wants to register it self
        - data: dict with client info (name etc)
        - request: the original request (data is already extracted as data and 
                   cannot be read again)
        
        e.g.: await s.send_cmd('192.168.0.103', 'test', 4,3,2,1,1, test_kw='testing')
              calss the method on_cmd_test of client with the args and kwargs
        """
        client_ip = request.remote
        name = self.rename(data.get('name'))
        data['name'] = name
        self.clients[client_ip] = data
        self.client_lookup[name] = client_ip
        print(f"client: {client_ip}:'{name}' - registered")
        return web.json_response(data)
    
    async def do_pcmd_ping(self, request, data):
        return
    
    async def do_pcmd_data(self, request, data):
        client_ip = request.remote
        print(client_ip, data)
  
if __name__ == "__main__":
    import threading as tr
    s = Server()
    tr.Thread(target=asyncio.run, args=(s.start(), )).start()