import aiohttp

from json import JSONDecodeError

class WebSocketHandler():
    """
    handles reading and writeing to aiohttp websockets
    """
    WS_CLOSE_CMD = 'close_cmd'              # command to close web socket
    client_ip = 'SERVER'

    HEART_BEAT_INTERVAL = 10                # ping interval to check if connection is alive
    MAX_MSG_SIZE = 4194304                  # max size of websocket message in bytes

    def __init__(self, client_ip='SERVER') -> None:
        self.ws = None
        self.client_ip = client_ip                          # for server to identify websocket
    
    async def make_connection(self, ws):
        self.ws = ws
        await self.websocket_reader()

    async def websocket_reader(self):
        # read
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    if msg.data == self.WS_CLOSE_CMD:
                        # await self.ws.close()
                        break
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print('ws connection closed with exception'
                            f' {self.ws.exception()}')

                try:
                    data = msg.json()

                except JSONDecodeError:
                    data = msg.data

                await self.on_ws_msg(self.client_ip, data)
        
        except TypeError as e:
            print(f"websocket reader error {type(e)}: {e}"
                   "\nNOTE: if error has 'None type cannot be used in await'\n"
                   "the issue is probably that on_ws_msg calls a sync function")
        
        except Exception as e:
            print(f"websocket reader error {type(e)}: {e}"
                  "\nError produced here might be in on_ws_msg function"
                  )
        
        finally:
            # CLEAN UP
            await self.ws.close()
            self.ws = None
            return await self.on_ws_close(self.client_ip)
    
    async def websocket_write(self, data):
        if isinstance(data, str):
            return await self.ws.send_str(data)
        elif isinstance(data, dict):
            return await self.ws.send_json(data)
        else:
            return await self.ws.send_bytes(data)
    
    async def on_ws_msg(self, origin, data):
        print(f'websocket msg received from {origin}: {data}')
        ...
        
    async def on_ws_close(self, origin):
        print(f'WebSocket {origin} Closed')