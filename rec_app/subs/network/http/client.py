from ctypes import resize
from email import header
import aiohttp
import asyncio

import ssl

from requests import head, session

from subs.network.http.websocket import WebSocketHandler

from inspect import isawaitable

class HttpClient(WebSocketHandler):
    client_path = './keys/client.pem'
    ca_path = './keys/ca.cer'

    boundary = 'WV-QQ-VW' # 'xxxx-boundary'

    server = ''

    def __init__(self,) -> None:
        self.session = None
        self.run = asyncio.Event()
    
    def start(self,):
        asyncio.run(self.aio_start())
    
    async def aio_start(self):
        self.run.set()
        await self.create_session()
        await self.connect_loop()
    
    async def connect_loop(self):
        while self.run.is_set():
            if self.server:
                try:
                    await self.connect()
                    await self.create_web_socket()

                except aiohttp.ClientConnectorError:
                    pass

            await asyncio.sleep(2)
        
        if self.session:
            await self.session.close()

    async def create_session(self):
        """
        creates session (connection with server)
        """
        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                                  cafile=self.ca_path,
                                                    )
        self.ssl_ctx.load_cert_chain(self.client_path)# '/path_to_client_public_key.pem', '/path_to_client_private_key.pem')
        self.ssl_ctx.check_hostname = False

        conn = aiohttp.TCPConnector(ssl=self.ssl_ctx)
        self.session = aiohttp.ClientSession(# self.server, 
                                             connector=conn,)
    
    async def connect(self):
        await self.post('ping', data=b'ping',
                        on_response=self.on_connect)

    async def on_connect(self, response):
        print(f'Connected to : {self.server}')

    async def unpack_response(self, response):
        if not response.ok:
            print("Status Error: ", response.status)
            return

        if response.content_type  == 'text/plain':
            return await response.text()
            
        elif response.content_type == 'application/json':
            return await response.json()
            
        else:
            # receive binary
            return await response.read()

    async def get(self, url):
        """
        request from url at server
        and return text, json or bytes in format detecteds
        """
        url = f"{self.server}/get/{url}"
        async with self.session.get(url) as response:
            print(f"requested url: {response.url}")
            
            print("Content-type:", response.content_type)

            data = await self.unpack_response(response)

            print(f"{response.content_length} bytes received"
                    f" {response.content_type}: {data[-100:] if data is not None else data}")

            return data

    async def post(self, 
                   url, 
                   data=None, 
                   on_response: callable=None,
                   ):
        """
        send small binary, json or text objects to url

        use on_response to set a function which is called when done
        """
        url = f"{self.server}/post/{url}"
        json_data = None
        if isinstance(data, dict):
            data, json_data = None, data 
        
        async with self.session.post(url, data=data, json=json_data) as response:
            data = await self.unpack_response(response)

            # run post functions
            if on_response is not None:
                response = on_response(response)
            
            return await response if isawaitable(response) else data
    
    async def send_file(self, filepath, rename='', compression='br'):
        with open(filepath, 'rb') as f:
            result = await self._send_big_object('/save/file',
                                        [f], 
                                        compression=compression, 
                                        rename=rename)
            print(await result.text())
    
    async def send_big_object(self, 
                              objects_list: list,
                              headers={}):
        """
        send big objects in chunks (should be packed in list)
        use headers to add custom headers or change other headers
        """

        result = await self._send_big_object('/receive/big-object',
                                             objects_list, headers=headers)
        print(await result.text())

    async def _send_big_object(self,
                               url,
                               obj_list, 
                               compression=None,
                               headers={},              # use to add or update headers
                               rename=''):
        """
        sends big objects in chunks.
        - url: url to post to
        - obj_list: iterable with objects, can be string, bytes, dict or file
        - compression: compression e.g. brotli, gzip or deflate # TODO test if works
        - rename: change filename to this when sending
        """
        url = f"{self.server}{url}"
        with aiohttp.MultipartWriter() as mpwriter:
            
            mpwriter.headers.update(headers)
            
            for obj in obj_list:
                if isinstance(obj, dict):
                    part = mpwriter.append_json(obj)
                # TODO add option to add form data using append_form

                else:
                    part = mpwriter.append(obj)
                
                if compression:
                    part.headers[aiohttp.hdrs.CONTENT_ENCODING] = compression
                
                if rename:
                    part.set_content_disposition('attachment', filename=rename)

            return await self.session.post(url, data=mpwriter)

    async def create_web_socket(self):
        """
        NOTE websocket reader & writer are inherited from WebSocketHandler
        """
        self.ws = await self.session.ws_connect(f'{self.server}/websocket',
                                                heartbeat=self.HEART_BEAT_INTERVAL,
                                                max_msg_size=self.MAX_MSG_SIZE)
        await asyncio.create_task(self.websocket_reader())

    async def stream_from_server(self, cmd, on_data:callable):
        """
        stream data from server and call callable with new data
        """
        url = f"/stream/{cmd}"
        await self._stream_from_server(url, on_data)# asyncio.create_task(self._stream_from_server(url, on_data))
    
    def stop_stream_in(self):
        self.run_stream.clear()

    async def _stream_from_server(self, 
                                  url, 
                                  on_data:callable):
        """
        load stream from server
        """
        url = f"{self.server}{url}"
        async with self.session.get(url) as response:
            # Create multipart reader from response
            global part, reader

            reader = aiohttp.MultipartReader.from_response(response)

            headers = response.content_type
            print(headers)

            i = 0
            task = None
            
            self.run_stream = asyncio.Event()
            self.run_stream.set()


            async for part in reader:
                # get body part readers from multipart reader:
                c_type = part.headers.get(aiohttp.hdrs.CONTENT_TYPE)
                size = part.headers.get(aiohttp.hdrs.CONTENT_LENGTH, '0')
                print(c_type, size)
                if (not self.run_stream.is_set() or part.at_eof() or 
                    (size=='0' and c_type == "application/octet-stream")):
                    print('stopped stream')
                    break
                
                print(f'{i}: ', c_type, size, size==0)

                if c_type == 'text/plain':
                    data = await part.text()

                elif c_type == 'application/json':
                    data = await part.json()
                
                else:
                    data = bytearray()
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        data.extend(chunk)

                result = on_data(data)
                if isawaitable(result):
                    if task is not None:
                        await task
                    task = asyncio.create_task(result)
                    
                print(f"{i:3.0f}: {data}\n"[-50:])
                i += 1

    async def stream_out(self, stream_name):
        await self._steam_out('/stream_in', stream_name)

    async def _steam_out(self, url, stream_name):
        """
        stream_name should be used to indicate 
        for the  make stream method 
        which stream has to be opened
        """
        url = f"{self.server}{url}/{stream_name}"

        stream  = await self.make_stream(stream_name)

        self.run_stream_out = asyncio.Event()
        self.run_stream_out.set()

        async for frame, header in stream:
            if not self.run_stream_out.is_set():
                break

            with aiohttp.MultipartWriter(boundary=self.boundary) as mpwriter:
                if header.get(aiohttp.hdrs.CONTENT_TYPE, '') == 'application/json':
                    mpwriter.append_json(frame, header)

                else:           
                    mpwriter.append(frame, header)
    
                # use append payload to add to first append and send object in parts
                await self.session.post(url, data=mpwriter)

    def stop_stream_out(self):
        self.run_stream_out.clear()

    async def make_stream(self, stream_name):
        """
        placeholder for functions that returns a async generator (see example)
        this is called with stream name from the client to request a stream
        it should return (content, header)
        """
        async def stream():
            while True:
                yield ('Streaming this data... ' * 0xFFFF, {aiohttp.hdrs.CONTENT_TYPE: 'text/plain',})
                await asyncio.sleep(1)
        return stream()



if __name__ == "__main__":
    import threading as tr
    c = HttpClient()
    c.server = 'https://0.0.0.0:55930'

    print("""
    ASYNC HTTP CLIENT
    to test synchronously use
    tr.Thread(target=c.start).start()
    
    or to run commands in ipython (e.g. await c.post('/test', 'test msg') ):
    await c.create_session() 
    await c.connect()
    """)


# TODO: check https://github.com/aiortc/aiortc for video streaming
