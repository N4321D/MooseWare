from subs.driver.interface_drivers.controller_template import Controller
from kivy.app import App
import json

class BroadCastController(Controller):
    """
    saves incoming broadcasts
    """
    
    async def start(self) -> None:
        await self.app.IO.NETWORK_READY.wait()

        if self.app.IO.client:
            self.device = self.app.IO.client
        else:
            self.device = self.app.IO.server
    
    async def run(self) -> None:
        await self._network.stop_flag.wait()
        self.disconnected.set()

    def _setup(self, *args, **kwargs) -> None:
        self.app = App.get_running_app()

    def _preprocess_data(self, data):
        data = json.loads(data)
        self.do(data)