from subs.network.multicast.multicast import BroadCast_MultiCast
from cryptography.fernet import Fernet, InvalidToken

import asyncio


class ServClientShared():
    """
    client and servers shared settings
    """
    HTTP_PORT = 0xDA7A
    BROADCAST_PORT = 0xABBA
    BOUNDARY = "WVv-|QQ|-vVW"
    KEY = b'O2dTXcCkL_H2jsUGZwRTRLzVEEdkFNEK7ljRtzY9Hm0='   # TODO set key in settings


    SERVER_ANNOUNCE_MSG = b"WVv-|QQ|-vVW"

    http_paths = {"ca_path": './keys/ca.cer',
                  "server_path": './keys/server.pem',
                  "client_path": './keys/client.pem',
                  "data_dir": './data/',
                  "save_path": './data/incoming/'}

    def __init__(self) -> None:
        self.encryption = Fernet(self.KEY)


    async def setup_broadcast(self):
        self.broadcast = BroadCast_MultiCast()
        self.broadcast.BROADCAST_PORT = self.BROADCAST_PORT
        self.broadcast.datagram_received = self.broadcast_received
        self.broadcast.error_received = self.broadcast_error_received
        self.broadcast.connection_lost = self.broadcast_connection_lost
        return asyncio.create_task(self.broadcast.start())
    
    async def broadcast_received(self, data, addr):
        if data == self.SERVER_ANNOUNCE_MSG:
            await self.on_register(data, addr)
        
        else:
            try:
                data = self.encryption.decrypt(data)
            except InvalidToken:
                print('received unencrypted data / decryption failed')
            await self.on_datagram(data, addr)
    
    async def write_broadcast(self, data, encrypt=True):
        if encrypt:
            data = self.encryption.encrypt(data)
        await self.broadcast.write_broadcast(data)
    
    async def write_multicast(self, data, encrypt=True):
        if encrypt:
            data = self.encryption.encrypt(data)
        await self.broadcast.write_multicast(data)


    async def broadcast_error_received(self, exc):
        print('broadcast udp err', exc)
    
    async def broadcast_connection_lost(self, exc):
        print('broadcast udp lost', exc)
    
    async def on_datagram(self, data, addr):
        print(f'Received from {addr}: {data}')
    
    async def on_register(self, data, addr):
        """
        called when server broadcast is received
        """
        pass