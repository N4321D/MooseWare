"""
UDP Broadcasting protocol

sends and receives multicast and broadcast messages

"""


import asyncio
import socket
import struct


class Broad_Multi_Cast_Prot:
    def __init__(self, parent):
        self.transport = None
        self.parent = parent
        self.loop = asyncio.get_running_loop()

    def connection_made(self, transport):
        self.transport = transport
        self.socket = self.transport.get_extra_info('socket')

        # Set the time-to-live for messages to 1 so they do not go past the
        # local network segment.
        # https://docs.oracle.com/cd/E19683-01/806-4125/6jd7pe6c6/index.html
        ttl = struct.pack('b', 32)  # value from 0 to 255 1= subnet, 32 is site
        self.socket.setsockopt(socket.IPPROTO_IP, 
                        socket.IP_MULTICAST_TTL, ttl)


    def datagram_received(self, data, addr):
        asyncio.create_task(self.parent.datagram_received(data, addr))

    def error_received(self, exc):
        asyncio.create_task(self.parent.error_received(exc))

    def connection_lost(self, exc):
        asyncio.create_task(self.parent.connection_lost(exc))

    def write_multicast(self, msg):
        self.transport.sendto(msg, (self.BROADCAST_ADDR, self.BROADCAST_PORT))
    
    def write_broadcast(self, msg):
        self.transport.sendto(msg, ('<broadcast>', self.BROADCAST_PORT))

class BroadCast_MultiCast():
    BROADCAST_PORT = 1910
    BROADCAST_ADDR = "239.255.255.250"
    
    def __init__(self) -> None:
        pass

    async def start(self):
        self.run_task = asyncio.create_task(self._setup())
        await self.run_task
            
    async def stop(self):
        print('stop now')
        self.run_task.cancel()
        self.sock.close()

    async def _setup(self):
        self.loop = asyncio.get_running_loop()
        self.stop_flag = asyncio.Event()
        prot = Broad_Multi_Cast_Prot(self)
        prot.BROADCAST_ADDR = self.BROADCAST_ADDR
        prot.BROADCAST_PORT = self.BROADCAST_PORT

        addrinfo = socket.getaddrinfo(self.BROADCAST_ADDR, None)[0]
        self.sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        
        except AttributeError:
            pass

        # setup multicast & join group:
        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        self.sock.bind(('', self.BROADCAST_PORT))
        group = socket.inet_aton(self.BROADCAST_ADDR)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # allow broadcast
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.transport, self.protocol = await self.loop.create_datagram_endpoint(lambda: prot,
                                                                sock=self.sock,)
        await self.stop_flag.wait()

    async def write_multicast(self, msg):
        return self.protocol.write_multicast(msg)
    
    async def write_broadcast(self, msg):
        return self.protocol.write_multicast(msg)

    async def datagram_received(self, data, addr):
        '''
        placeholder which is called when data is received
        '''
        pass

    async def error_received(self, exc):
        '''
        placeholder which is called when error
        '''
        pass

    async def connection_lost(self, exc):
        '''
        placeholder which is called when connection is lost
        '''
        pass


if __name__ == "__main__":
    import threading as tr
    br = BroadCast_MultiCast()
    tr.Thread(target=asyncio.run, args=(br.start(), )).start()