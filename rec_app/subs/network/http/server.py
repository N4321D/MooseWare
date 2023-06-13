import aiohttp
from aiohttp import web

import os
import asyncio

import ssl

import logging

import urllib.parse

from subs.network.http.websocket import WebSocketHandler

routes = web.RouteTableDef()


class HttpServer():
    PORT = 8443
    INTERFACE = None

    ca_path = '../../../keys/ca.cer'
    server_path = '../../../keys/server.pem'
    data_dir = '../../../data/'
    save_path = '../../../incoming/'

    boundary = 'WV-QQ-VW' #'xxxx-boundary'

    def __init__(self) -> None:
        self.ws = {}              # websockets placeholder
        self.run_stream = asyncio.Event()
        self.stop_flag = asyncio.Event()
        self.HEART_BEAT_INTERVAL = WebSocketHandler.HEART_BEAT_INTERVAL
        self.MAX_MSG_SIZE = WebSocketHandler.MAX_MSG_SIZE

    async def _create_context(self):
        self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, 
                                                  cafile=self.ca_path)
        self.context.load_cert_chain(self.server_path)
        self.context.verify_mode = ssl.CERT_REQUIRED

    async def start(self):
        self.app = web.Application(logger=logging.getLogger('kivy'))

        await self.add_routes()

        print('start')

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        await self._create_context()
        self.site = web.TCPSite(self.runner, 
                                self.INTERFACE, 
                                self.PORT, 
                                ssl_context=self.context,
                                shutdown_timeout=120,
                                )

        print('setup finished')
        await self.site.start()
        
        print('site started')
        await self.stop_flag.wait()
    
    async def stop(self):        
        # wait for finish signal
        self.stop_flag.set()
        await self.runner.cleanup()
        print('server closed')

    async def add_routes(self):
        self.app.add_routes([
                web.get('/get/{cmd}', self.get_cmd, name='get-cmd'),
                web.post('/post/{cmd}', self.post_cmd),
                web.get('/websocket', self.websocket_handler),
                web.post('/save/file', self.save_file),
                web.post('/receive/big-object', self.receive_big_object),
                web.get('/stream/{cmd}', self.stream),
                web.post('/stream_in/{cmd}', self.receive_stream),

                web.static('/file-browser', self.data_dir, show_index=True),                
                ])  # host files on url/see_static

    async def unpack_request(self, request):
        if request.content_type == 'text/plain':
            return await request.text()
        elif request.content_type == 'application/json':
            return await request.json()
        else:
            return await request.read()

    async def get_cmd(self, request):
        cmd = request.match_info.get('cmd', None)
        if cmd is None:
            print('Err no command')
            return web.HTTPBadRequest()

        else:
            response = await self.on_get_cmd(cmd, request) or web.HTTPOk()
            return response
    
    async def on_get_cmd(self, cmd, request):
        print(f"request from {request.remote} - {cmd}")
        return web.HTTPOk()
  
    async def post_cmd(self, request):
        cmd = request.match_info.get('cmd', None)
        if cmd is None:
            print('Err no command')
            return web.HTTPBadRequest()

        data = await self.unpack_request(request)

        response = await self.on_post_cmd(cmd, request, data)
        
        return response if response is not None else web.HTTPOk()
    
    async def on_post_cmd(self, cmd, request, data):
        print(f"Post from {request.remote}: {cmd} - {request.content_type} - {str(data):.50s}")
        return web.HTTPOk()

    async def websocket_handler(self, request):
        """
        NOTE websocket reader & writer are inherited from WebSocketHandler
        """
        client_ip = request.remote
        ws = web.WebSocketResponse(heartbeat=self.HEART_BEAT_INTERVAL,
                                    max_msg_size=self.MAX_MSG_SIZE)
        await ws.prepare(request)
        self.ws[client_ip] = WebSocketHandler(client_ip)
        self.ws[client_ip].on_ws_msg = self.on_ws_msg
        self.ws[client_ip].on_ws_close = self.on_ws_close
        await self.ws[client_ip].make_connection(ws)

    async def on_ws_msg(self, origin, data):
        print(f'HTTP Server websocket msg received from {origin}: {data}')

    async def on_ws_close(self, origin):
        print(f'HTTP Server websocket {origin} closed')

    async def save_file(self, request):
        """
        saves file in self.savepath
        """
        result = await self._receive_big_object(request, save=True)
        if result:
            return web.HTTPOk()
        else:
            return web.HTTPError()

    async def receive_big_object(self, request):
        """
        saves file in self.savepath
        """
        result = await self._receive_big_object(request, save=False)
        if result:
            await self.on_big_object(request, result)
            return web.HTTPOk()
        else:
            return web.HTTPError()
    
    async def receive_stream(self, request):
        cmd = request.match_info.get('cmd', None)
        result = await self._receive_big_object(request, save=False, stream=True)
        if result:
            await self.on_stream(result, cmd)
            return web.HTTPOk()
        else:
            return web.HTTPError()

    async def _receive_big_object(self, request, save=False, stream=False):
        
        async for field in (await request.multipart()):
            content = field.headers.get(aiohttp.hdrs.CONTENT_TYPE)
            size = int(field.headers.get(aiohttp.hdrs.CONTENT_LENGTH))
            name = urllib.parse.unquote(field.filename) if field.filename else ''

            print(f"\nIncoming {'file' if name else 'data'}:"
                  f" {name} - {content} - {size/1e6:.2f} MB\n")

            if name and save:
                os.makedirs(self.save_path, exist_ok=True)
                full_path = os.path.join(self.save_path, name)
                f = open(full_path, 'wb')

            recv_size = 0
            result = bytearray()

            if content == 'application/json':
                result = await field.json()
                return result

            elif content.startswith('text/plain'):
                result = await field.text()
                return result

            else:
                while True:
                    chunk = await field.read_chunk()
                    recv_size += len(chunk)

                    if not chunk:
                        if name and save:    
                            f.close()
                            print(f'file: {full_path} received: {recv_size/1e6:.2f} MB')
                        break
                    
                    if name and save:
                        result = f.write(chunk)

                    else:
                        result.extend(chunk)

            if recv_size == size:
                return result

            else:
                print('File not received completely')
                if name and save:
                    os.remove(full_path)
                return False

    async def on_big_object(self, request, data):
        print(f'result received from {request.origin}, size: {len(data)/1e6:.2f} MB'
              f"{request.headers}")

    async def on_stream(self, data, stream_name):
        print(f"Stream incoming: {stream_name}")

    async def stream(self, request):
        print(f"From: {request.remote}")
        cmd = request.match_info.get('cmd', None)

        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={'Content-Type': 
                        f'multipart/x-mixed-replace;boundary={self.boundary}',
                     },
            )
        
        await response.prepare(request)

        i = 0
        stream = await self.make_stream(cmd)

        self.run_stream.set()

        async for frame, header in stream:  
            # NOTE: you have to declare the writer with every loop, 
            # otherwise data gets send multiple times
            if not self.run_stream.is_set():
                break

            with aiohttp.MultipartWriter(boundary=self.boundary) as mpwriter:

                if header.get(aiohttp.hdrs.CONTENT_TYPE, '') == 'application/json':
                    mpwriter.append_json(frame, header)

                else:           
                    mpwriter.append(frame, header)
    
                # use append payload to add to first append and send object in parts
                await mpwriter.write(response, close_boundary=False)

                print(f'frame {i}')
                i+=1

        # write eof
        mpwriter.append(b'')
        await mpwriter.write(response, close_boundary=True)
        
        self.run_stream.clear()
        return web.HTTPOk()

    def stop_stream(self):
        self.run_stream.clear()

    async def make_stream(self, stream_name):
        """
        placeholder for functions that returns a async generator (see example)
        this is called with stream name from the client to request a stream
        """
        print('TODO implement stream making protocol here')
        async def stream():
            while True:
                # with open('./static/camel.jpg', 'rb') as f:
                #     yield (f.read(), {'Content-Type': 'image/jpeg', 
                #                       })

                yield ('streaming test..... '*100, {'Content-Type': 'text/plain',
                                                    })

                # with open('./static/camel_hat.jpg', 'rb') as f:
                #     yield (f.read(), {'Content-Type': 'image/jpeg',
                #                       })

                yield ({i: i**2 for i in range(3)}, {aiohttp.hdrs.CONTENT_TYPE: 'application/json', 
                                                     })
                await asyncio.sleep(1)

        return stream()


if __name__ == '__main__':
    import threading as tr
    s = HttpServer()
    tr.Thread(target=asyncio.run, args=(s.start(), )).start()

# TODO: check https://github.com/aiortc/aiortc for video streaming


"""
NOTE:

http headers:
CONTENT TYPE:
All possible values of HTTP Content-type header:

    Application	
        application/EDI-X12
        application/EDIFACT
        application/javascript
        application/octet-stream
        application/ogg
        application/pdf
        application/xhtml+xml
        application/x-shockwave-flash
        application/json
        application/ld+json
        application/xml
        application/zip
        application/x-www-form-urlencoded

    Audio	
        audio/mpeg
        audio/x-ms-wma
        audio/vnd.rn-realaudio
        audio/x-wav

    Image	
        image/gif
        image/jpeg
        image/png
        image/tiff
        image/vnd.microsoft.icon
        image/x-icon
        image/vnd.djvu
        image/svg+xml
        
    Multipart	
        multipart/mixed
        multipart/alternative
        multipart/related (using by MHTML (HTML mail).)
        multipart/form-data
    
    Text	
        text/css
        text/csv
        text/html
        text/plain
        text/xml

    Video	
        video/mpeg
        video/mp4
        video/quicktime
        video/x-ms-wmv
        video/x-msvideo
        video/x-flv
        video/webm
    
    VND	
        application/vnd.oasis.opendocument.text
        application/vnd.oasis.opendocument.spreadsheet
        application/vnd.oasis.opendocument.presentation
        application/vnd.oasis.opendocument.graphics
        application/vnd.ms-excel
        application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        application/vnd.ms-powerpoint
        application/vnd.openxmlformats-officedocument.presentationml.presentation
        application/msword
        application/vnd.openxmlformats-officedocument.wordprocessingml.document
        application/vnd.mozilla.xul+xml
"""