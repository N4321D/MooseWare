"""
Input out between GUI and recording

controls recording, saving and plotting of the data

# TODO: send new data over network if client

# TODO: adapt saver blocks to be less than datalength
# TODO: limit recording name characters
# TODO: link compression options in app to saver
"""

import asyncio
from subs.gui.vars import SETTINGS_VAR
from functools import partial
import numpy as np
import threading as tr
from datetime import timedelta, datetime
import time
import subs.network.client as nw_client     # import network client
import subs.network.server as nw_server     # import network client

from subs.recording.saver import Saver

from subs.driver.interface_factory import InterfaceFactory

from subs.recording.buffer import SharedBuffer
from kivy.properties import (BooleanProperty, NumericProperty,
                             DictProperty, ListProperty,
                             BoundedNumericProperty, StringProperty,
                             ConfigParserProperty)
from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher

import traceback

# create logger
try:
    from subs.log import create_logger
    logger = create_logger()

except:
    logger = None


def log(message, level="info"):
    cls_name = "INPUT_OUTPUT"
    try:
        # change CLASSNAME here
        getattr(logger, level)(f"{cls_name}: {message}")
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")


# lines of notes in memory,
NOTES_LENGTH = 2000

# PARAMETERS TO REMOVE FROM PLOT CHOICES
REMOVE_PARS = {"us", "sDt", "time"}


def proc_async_exceptions(results):
    """
    Processes results from asyncio.gather and extracts and logs exceptions 
    with traceback. NOTE: asyncio.gather must be called with the 
    return_exceptions=True keyword

    This function iterates over the results list returned by asyncio.gather and 
    checks if any of the items is an exception object. If so, it calls the 
    _create_tb function to format and log the exception information using the 
    traceback module.

    Args:
        results (list): A list of results or exceptions returned by 
        asyncio.gather.

    Returns:
        None
    """
    (*map(_create_tb, results),)


def _create_tb(result):
    """ 
     Formats and logs an exception object using the traceback module.

    This function takes an exception object and uses the traceback.format_exception 
    function to create a string with the formatted exception information. 
    It then uses the log function to log the string with a warning level.

    Args:
        result (Exception): An exception object.

    Returns:
        None
    """
    if isinstance(result, Exception):
        tb = "\n".join(traceback.format_exception(result))
        log(f"Error in async.gather results: {tb}", "error")


class InputOutput(EventDispatcher):
    # placeholder for app
    app = None

    # main vars
    dt = {'plotting': 1,
          }                                                              # Wait times for input & plot loop
    recording_name = ConfigParserProperty("Untitled", "recording",
                                          "recording_name", "app_config",
                                          val_type=str,)                 # Name of the curren recording

    # Dictionary with connected sensors for current interface
    sensors = DictProperty({})

    # list with plottable pars (to choose in graph)
    choices = ListProperty([])

    # dictionary with connected interfaces
    interfaces = DictProperty({})
    interfaces_names = DictProperty({})  # lookup table for interface names

    # plot micro or internal sensors
    selected_interface = StringProperty("")

    rec_pars = DictProperty({'samplerate': 0,
                             'emarate': 0})                             # pars from recorder

    # placeholder for saver
    sav = None
    # interval to create new file
    new_file_interval = timedelta(days=1)

    # network vars:
    # ip of client to get data from
    client_ip = ''
    # list with all client ips
    client_ip_list = ListProperty([])
    # placeholder for server class
    server = None
    # placeholder for client class
    client = None
    # indicates to client to send data/video
    sending = False
    # blocksize (in data items) to send over network
    NW_BLOCK = 32000
    NETWORK_READY = asyncio.Event()

    # plotting vars:
    # list with the graphs for plotting the data
    graphs = []
    yzoom = BoundedNumericProperty(0.0, min=0, max=10000,
                                   errorhandler=lambda x: 10000
                                   if x > 10000 else 0)                 # zoom of Y ax in %
    # time frame to plot
    secondsback = NumericProperty(10)

    # Switches & events
    # Event to signal that app is closing
    EXIT = asyncio.Event()
    # Thread with plot functions
    plot_tr = None
    # Kivy clock.schedule_once call to plot
    plot_event = None
    # Kivy Clock event for drawing plots
    draw_event = None
    # bool to indicate if data recording running or not
    running = BooleanProperty(False)
    # bool to indicate if plotting is on or not
    plotting = BooleanProperty(True)

    def __init__(self) -> None:
        self.app = App.get_running_app()

        # change client name on name change
        self.app.bind(
            setupname=lambda *_: self.client.rename(self.app.setupname) if self.client else ...)

        # create shared memory
        self.shared_buffer = SharedBuffer()
        self.buffer = self.shared_buffer.buffer
        self.data_structure = self.shared_buffer.data_structure
        self.get_buf = self.shared_buffer.get_buf

        self.create_notes()

        # limit seconds back
        def limit_secondsback(_, x):
            x = max(1, min(x, self.app.rec_vars.data_length))
            if self.secondsback != x:
                self.secondsback = x

        self.bind(secondsback=limit_secondsback)

        Clock.schedule_once(self.__kv_init__, 0)

        self.async_main_coro_task = asyncio.create_task(self.main_coro())

    def __kv_init__(self, dt):
        """
        Init launched after kivy app is built
        """
        self.app.root.bind(UTC=self.update_feedback)
        self.add_note(f"{SETTINGS_VAR['Main']['title']} "
                      f"- {SETTINGS_VAR['Main']['app_version']} ")

    async def main_coro(self):
        """
        This is the main async coroutine will initiate and run asynchronous tasks, 
        including setting up the network, plot creation, and data processing. 
        """
        tasks = set()
        tasks.add(self.plot())

        # setup network
        tasks.add(self.serv_client())

        # start interface factory
        tasks.add(self.interface_loop())

        # async execute all tasks here
        proc_async_exceptions(
            await asyncio.gather(*tasks,
                                 return_exceptions=True))

        # ASYNC CLEANUP
        # stop server
        if self.server is not None:
            await self.server.stop()

        if self.client is not None:
            await self.client.stop()

    def clear(self):
        """
        clear data from memory before new recording
        """
        self.shared_buffer.remove_parameter('data')

    def start_recording(self, save=True):
        """
        Start recording and set up all related variables and parameters.

        Args:
            save (bool, optional): Flag indicating whether to save the data or not. Defaults to True.

        Attributes:
            sav (Saver): Saver object.
            running (bool): Flag indicating if recording has started.
            shared_buffer (data structure): Shared memory buffer containing recorded data.
            app (App): The main application object.
        """
        self.clear()

        self.add_note(f"{SETTINGS_VAR['Main']['title']} "
                      f"- {SETTINGS_VAR['Main']['app_version']}: "
                      f"{self.recording_name}")
        self.add_note(f"Recording Started")

        if not self.client_ip:
            # create saver
            if save:
                self.sav = Saver(recname=self.recording_name,
                                 NEW_FILE_INTERVAL=self.new_file_interval)
                self.sav.start()

            else:
                self.sav = None

            # start controllers
            for dev_name in self.interfaces:
                if self.interfaces[dev_name].record:
                    self.interfaces[dev_name].start_stop(True)

            # update links to shared memory for new parameters
            self.shared_buffer.check_new()

        self.running = True

    def stop_recording(self):
        """
        This function will stop the Recorder instance by calling its `stop` method and 
        discarding any further data points from being added to the buffer. 
        It will also stop the Saver instance if one was running. 
        Finally, it will join on the `Recorder.process`, and add a note that the recoring
        has stopped
        """
        if not self.client_ip:
            self.stop_all_stims()

            for dev_name in self.interfaces:
                self.interfaces[dev_name].start_stop(False)

            if self.sav:
                self.sav.stop()

            self.add_note(f"Recording stopped")

        self.running = False

    def chip_command(self, 
                     interface, 
                     chip, 
                     key,
                     value, 
                     *args, **kwargs):
        """
        Run a function of the chip driver with args and kwargs
        - interface: interface to send command to; use None to send to all
        - chip: chip to trigger function on
        - key: key to send
        - value: value to send
        - kwargs: keyword arguments to put in function

        example:
        `chip_command("LED_chip", 'set_led', 30, color='blue')` sets leds on on 
            this driver to 30% blue light 
        """

        if interface not in self.interfaces and interface is not None:
            return
        
        interfaces = [interface] if interface else self.interfaces
        [self.interfaces[i].write(
            {chip: {key:value}}) for i in interfaces
            if chip in self.interfaces[i].sensors  # only send if chip is in interface
            ]

    # PLOT FUNCTIONS:
    async def plot(self, *_):
        """
        Continuously plot data and update various parameters while the EXIT flag 
        is not set.

        The function `plot` continuously retrieves data from `self._data_in` and
        updates various parameters and statistics, such as the 
        `self.client_ip_list`, the `self.app.setupname`, and the `self.rec_pars`. 
        The function also continuously updates the plot with the latest 
        data. The function runs in an infinite loop as long as the `self.EXIT` 
        flag is not set.

        runs/returns `self.exit()` at the end
        """
        while not self.EXIT.is_set():
            # check if enough diskspace:
            if self.sav is not None and self.sav.disk_full:
                self.stop_recording()
                log("Disk almost full, recording stopped", "warning")
                self.app.popup.load_defaults()
                self.app.popup.buttons = {"OK": {}}
                self.app.popup.title = (
                    "DISK FULL:\nRecording Stopped")
                self.app.popup.open()
                return

            tasks = set()
            self.shared_buffer.check_new()
            if self.running:
                tasks.add(self._get_data_and_plot(graphs=self.graphs))
                tasks.add(self._update_rec_pars())

            else:
                tasks.add(self.update_plot_pars())

            # update stats
            if self.server is not None:
                self.client_ip_list = list(self.server.client_lookup.keys())

            if self.client is not None and self.client.name:
                self.app.setupname = self.client.name

            # wait for all tasks to finish:
            proc_async_exceptions(await asyncio.gather(*tasks,
                                                       return_exceptions=True))

            plot_dt = self.dt['plotting']
            if self.secondsback > 300:
                plot_dt *= 2

            await asyncio.sleep(plot_dt)

        return self.exit()

    async def update_plot_pars(self, *_):
        self._update_plot_pars()

    def _update_interface_names(self, *_):
        names = {}
        for ID, dev in self.interfaces.items():
            name = dev.__dict__.get("name", ID)
            if name in names:
                # device name used already: RENAME!
                name = f"{name}\n({ID})"
                dev.rename(name)

            names[name] = dev

        if names != self.interfaces_names:
            self.interfaces_names.clear()
            self.interfaces_names.update(names)

    def _update_plot_pars(self, *_):
        """
        Check connected intrefaces, sensors and status
        """
        self._update_interface_names()

        interface = self.interfaces.get(self.selected_interface)
        if not interface:
            return

        if interface.ID != self.selected_interface:
            self.interfaces[interface.ID] = self.interfaces.pop(self.selected_interface)
            self.selected_interface = interface.ID

        sensors = {k: v for k, v in interface.sensors.items() if v.connected}
        pars = interface.parameters

        # TODO: extra pars in sensor driver such as off or combinations of 2 (e.g. pressure = pressure int - pressure ext)

        # Create list of plottable sensors
        choices = sorted(
            set(pars).difference(REMOVE_PARS),
            key=lambda x: ("GPIO" in x, x),
        ) + ["Off"]

        if sensors != self.sensors or choices != self.choices:
            # do only when new sensor connected/disconnected
            self.sensors.clear()
            self.sensors.update(sensors)
            self.choices = choices

    async def _update_rec_pars(self, *_):
        """
        get the last parameters from the recorder, including:
        - run: bool, is it running or not
        - samplerate: float, current sample rate
        - minrate: float, min limit sample rate
        - maxrate: float, max limit sample rate
        - emarate: float, current exponential avg theoretical max sample rate
        """
        if self.interfaces:
            dev = self.interfaces[self.selected_interface]
            _new_pars = {
                "samplerate": dev.current_rate,
                "emarate": dev.emarate,
                "run": dev.run,
            }
            self.rec_pars.update(_new_pars)

    def get_time_back_data(self, seconds_back, par=...):
        """
        get last recorded data upto x seconds back
        - seconds_back: time from last recorded data back to retrieve
        - par: specific parameter to retrieve, if not defined all 
               pars are returned
        """
        if 'time' not in self.buffer['data'].dtype.fields:
            log('x-axis: time parameter not in rec data'
                ' -> unable to retrieve data', "warning")
            return

        return self.shared_buffer.get_time_back('data', seconds_back,
                                                time_sub_par='time', subpar=par)

    async def _get_data_and_plot(self, graphs=None):
        """
        sets plot data in graphs, graphs must be:
        [('parameter', graph1, kwargs),
        ('parameter', graph2, kwargs), etc.]
        """
        interface = self.interfaces.get(self.selected_interface)
        if not interface:
            log("Interface {interface} not found in interfaces for plotting", "debug")
            return
        
        plot_buff_name = interface.get_buffer_name()

        if ((not self.plotting
                and not (self.sending and self.client))
            or not graphs
                or plot_buff_name not in self.buffer):
            return

        if 'time' not in self.buffer[plot_buff_name].dtype.fields:
            log('x-axis: time parameter not in rec data'
                ' -> unable to plot data', "error")
            return

        tasks = set()
        for graph in graphs:
            data = self._getdata(graph[0], out_len=graph[1].size[0],
                                 buff_block_name=plot_buff_name)

            if data is None or data.size == 0:
                log('no data to plot', "debug")
                continue

            if self.sending:
                # TODO: check
                # Send data over network
                tasks.add(self.send_data(data))

            if not self.plotting:
                continue

            tasks.add(self._plotdata(data,
                                     graph[1],
                                     **graph[2]))

        proc_async_exceptions(
            await asyncio.gather(*tasks, return_exceptions=True)
        )

    async def _plotdata(self,
                        data,                               # data to plot
                        graph,                              # input graph to change
                        **kwargs):
        """
        Wrapper function to async call plot from graph

        Args:
            data (np.recarray/np.structarray): numpy array with data, first par 
                                               should be x, 2nd -> nth Y traces
            graph (Graph): Graph object to plot data in

        Kwargs:
            passed to plot function of graph e.g:
                linecolor=(1,0,1,1), clearplot=True etc.
        """
        graph.plot(data, yzoom=self.yzoom / 100, **kwargs)

    def _getdata(self, par, out_len=None, buff_block_name="data"):
        """
        gets data and conversion function
        - par:  parameter to get data for
        - outlen: desired length of ouput (by decimation)
        """
        par = ['time', par]

        # exceptions for specific sensors
        # TODO: move the exceptions and functions to different file, maybe driver?
        if par[-1] == "OIS_SIG":
            par.append('OIS_STIM')

        # Get Data
        try:
            out = self.shared_buffer.get_time_back(
                seconds_back=self.secondsback,
                time_sub_par="time",
                par=buff_block_name,
                subpar=par).copy()
            return out

        except (KeyError, AttributeError) as e:
            log(f"Parameter not in memory or no data yet: {e}", 'warning')

    # Interfaces
    async def interface_loop(self):
        # create interface factory
        self.interface_factory = InterfaceFactory(
            on_connect=self.connect_interface,
            on_disconnect=self.disconnect_interface,
            IO=self,
            EXIT=self.EXIT,
            interfaces=self.interfaces,
        )
        # start scan loop
        await self.interface_factory.scan()

    def connect_interface(self, interface):
        self.interfaces[interface.ID] = interface
        interface.start_stop(False)   # force stop
        self.selected_interface = interface.ID

    def disconnect_interface(self, interface):
        if interface.ID in self.interfaces:
            del self.interfaces[interface.ID]

    def toggle_interface(self, interface, *args):
        if self.selected_interface != interface:
            self.selected_interface = interface
            self._update_plot_pars()

    def stop_all_stims(self, *args):
        """
        (Force) Stop all stimulation by sending stim 0, 0 to all sensors
        """

        for m in self.interfaces.values():
            for s in m.sensors.values():
                for sc in s.stim_control.values():
                    try:
                        sc.stop_stim() 
                    except:
                        pass

        for s in self.sensors.values():
            if hasattr(s, "stim_control"):
                for sc in s.stim_control.values():
                    try:
                        sc.stop_stim() 
                    except:
                        pass

    def _proc_data(self, par, data, dtype=None, shape=None):
        """
        processes incoming data from clients (np arrays as bytes strings)
        - par:      name of the parameter
        - data:     data as np.array.tobytes()
        - dtype:    np.dtype (list with dtypes for structured array)
        - shape:    shape of array (only required if multiple dim)
        """
        data = np.frombuffer(data, dtype=dtype).reshape(shape)
        _max_len = self.rec_pars['samplerate'] * self.app.rec_vars.data_length

        if shape is not None:
            max_shape = (_max_len,) + shape[1:]
        else:
            max_shape = (_max_len,)

        if par not in self.buffer:
            # create buffer
            self.shared_buffer.add_parameter(par, dtype, *max_shape)

        self.shared_buffer.add_to_buf(par, data)

    async def send_data(self, data):
        # TODO: "send data here, nbytes: {data.nbytes}"

        if self.client is not None:
            return self.client.send_data({'type': 'DATA',
                                          'data': data},
                                         headers={'MOOSE': {'type': 'DATA'}})

        if self.server is not None:
            # TODO prepare get for client and send client to do get request"
            pass

    def receive(self):
        if self.server is not None and self.client_ip != '':
            # send data when running as server
            return self.server.get_data(self.client_ip)

        elif self.client is not None:
            return self.client.get_data()

    async def send_var(self, scr, var, val=None, ar=(), kw={}, target=None):
        """
        send a variable or execute a remote function
        - scr: screen or main class where the function or variable is located (e.g. app or Record)
        - var: the variable to change, use dots for subclasses (e.g. ids.startbutt.text)
        - val: new value if var is not a function
        - ar:  args to execute var with if var is a function
        - kw:  kwargs to execute var with if var is a function

        example:
        1. send_var('Record', 'ids.startbutt.text', val='STOP') changes the text of the 
           start button to stop on the record screen
        2. send_var('Record', 'test', ar=[1,2,3]) runs function test with args 1, 2, 3
        """
        msg = {'type': 'VAR',
               'scr': scr,
               'var': var,
               'val': val,
               'ar': ar,
               'kw': kw,
               }

        if self.server is not None:
            await self.server.send_ws(target, msg)

        if self.client is not None:
            await self.server.send_ws(msg)

    async def serv_client(self):
        """
        Sets up a server or client instance based on the app configuration.

        If the app is configured as a server, it creates a nw_server.Server 
        object and assigns it to self.server. It also sets up callbacks for 
        handling client disconnection, websocket messages, and big objects. 
        It sets self.client to None and returns the result of calling 
        self.server.start().

        If the app is configured as a client, it creates a nw_client.Client 
        object and assigns it to self.client. It also sets its name attribute 
        to the app setupname. It sets self.server to None and returns the result 
        of calling self.client.start().
        """
        if self.app.SERVER:
            self.server = nw_server.Server()
            self.server.on_client_disconnected = partial(
                self.switch_client, None)
            self.server.on_ws_msg = self.proc_cmds
            self.server.on_big_object = self.proc_cmds
            self.client = None
            start = self.server.start()

        else:
            self.client = nw_client.Client()
            self.client.name = self.app.setupname
            self.server = None
            start = self.client.start()
        await start
        self.NETWORK_READY.set()

    def switch_client(self, client, *args):
        if client in self.client_ip_list:
            # disconnect previous client
            self.server.send_data(
                ("VAR", ('app', 'IO.sending', (False, ))))  # send disconnect
            self.clear()
            # connect new client:
            self.client_ip = self.server.clients[self.server.client_lookup[client]]
            self.server.active_client = self.client_ip
            self.server.send_data(("CONNECT", None))
            self.app.setupname = client

        elif client is None:
            # if connection lost
            log(f"Lost Connection with client: <{self.app.setupname}>", 'info')
            self.clear()
            self.client_ip = ''
            self.server.active_client = ''
            self.app.setupname = "SERVER"
            if self.running:
                self.app.root.ids.scrman.get_screen("Record").start()
            self.app.root.ids.client_select.text = "Connection Lost"

    def set_var(self, scr, var, val=None, ar=(), kw={}):
        """
        triggers method of a screen or childclass of app 
        or sets a var
        based on screen name and var/method name. A dot can be used
        to indicate subclasses/methods (e.g. "IO.set_var" or 
        "rec.ids.splot1.text")

        - scr: screen name (or main class)
        - var: variable/function name (can be subclass seperated by dots)
        - val: value to set
        - ar:  args if var is a callable
        - kw:  kwargs is var is a callable

        """

        if scr == 'app':
            scr = self.app

        elif scr == "RootWidget":
            scr = self.app.root

        else:
            # if var is in screen
            try:
                scr = self.app.root.ids.scrman.get_screen(scr)

            except Exception as e:
                log(f"Cannot find screen {scr}; {e}", "error")
                return

        # Extract sub class commands etc:
        cls_list = var.split('.')

        target = scr
        try:
            for cls in cls_list:
                last_var = target
                # iterate through child classes until par is found
                target = getattr(target, cls)

            if callable(target):
                # call method
                target(*ar, **kw)

            if isinstance(target, dict):
                # if dictionary and keyword
                target.update(val)

            else:
                # set variable
                setattr(last_var, cls_list[-1], val)

        except Exception as e:
            log(
                f"Cannot set incoming var/call function: {scr}.{var}: {ar} {kw} {val}\n-   {e}", "warning")

    async def proc_cmds(self, origin, data):

        """
        this function processes network data

        commands must be a dictionary with:

        # set variable or call function:
        VAR:
        {'type': 'VAR',
         'scr':  the screen or main class where the var is 
         'var':  the variable or function to call
         'val':  the new value
         'ar':   list with args if var is a function
         'kw':   dict with kwargs if var is a function
        }

        """
        if not data:
            return

        if not isinstance(data, dict):
            print({f"IO.proc_cmd received not a dict, {data}"})
            print(origin.headers)
            return

        print(origin, data)

        cmd = data.get('type')

        if not cmd:
            return

        if cmd == 'VAR':
            self.set_var(data.get('scr'),
                         data.get('var'),
                         ar=data.get('ar', []),
                         kw=data.get('kw', {}),
                         val=data.get('val'))

        elif cmd == 'DATA':
            # TODO: process incoming plot data here')
            pass
            # Send only graph data not full data

        elif cmd == 'CONNECT':
            self.sending = True     # client should start sending data
            # list of pars to send on connection:
            self.send_var('app', 'IO.sensors', val=dict(self.sensors))
            self.send_var('app', 'IO.choices', val=list(self.choices))
            self.send_var('app', 'IO.running', val=bool(self.running))
            self.send_var('app', 'IO.recording_name',
                          val=str(self.recording_name))
            self.send_var('app', 'stim.protocol', val=self.app.stim.protocol)
            self.send_var("Record", 'ids.splot1.text', val=str(
                self.app.root.ids.scrman.get_screen('Record').ids['splot1'].text))
            self.send_var("Record", 'ids.splot2.text', val=str(
                self.app.root.ids.scrman.get_screen('Record').ids['splot2'].text))
            self.send_var("Video", 'ids.vid_play.recording', val=bool(
                self.app.root.ids.scrman.get_screen('Video').ids.vid_play.recording))

        else:
            log(f"Command from {origin} not found: {data}", "error")

    # NOTES
    def create_notes(self):
        # create new notes if unavailable
        if 'notes' in self.buffer:
            return

        self.shared_buffer.add_parameter('notes',
                                         [('time', 'f8'), ('note', 'S1024')],
                                         NOTES_LENGTH)

    def add_note(self, note, time_stamp=0.0, interface=None):
        """
        add note to notes in file and update feedback box

        Args:
            note (str): note
            time_stamp (float, optional): timestamp for note, if nothing is entered, current time will be used
            interface: interface where the note is linked to, if None the currently selected interface will be used
        """
        time_stamp = time_stamp or time.time()
        note = f"{interface or self.selected_interface}: {note}"   # add selected interface to note
        self.shared_buffer.add_1_to_buffer('notes', (time_stamp, note))
        self.update_feedback()

    def update_feedback(self, *args):
        """
        Update feedback text on new notes or switch between utc and local time
        """
        _notes = self.get_buf('notes', subpar=['time', 'note'], n_items=3)

        if self.app.root.UTC:
            _dt_f = datetime.utcfromtimestamp
        else:
            _dt_f = datetime.fromtimestamp

        # covert timestamp to readable format zip notes and timestamps & limit charaters per line
        def convert_note(t, n):
            if not n:
                return " "
            n = n.decode()
            n = n.replace(f"{self.selected_interface}: ", "")
            return f"{n[:19]} {_dt_f(t).strftime('%X')}"

        _text = map(convert_note,
                    _notes['time'], _notes['note'])

        self._set_feedback_txt(_text)

    def clear_notes(self):
        """
        clears notes
        NOTE: this is not needed for new recordings, because
        unsaved notes will be included in new files but saved notes not
        and if everything works all notes should be saved
        """
        self.shared_buffer.clear_parameter['notes']

    def _set_feedback_txt(self, txt_list, *_):
        _txt = "\n".join(txt_list)
        self.app.root.ids.feedback.text = f"[ref=notes]{_txt}[/ref]"

    def exit(self,):
        """
        runs on exit to clean up
        async clean is done in main_coro
        """
        self.stop_all_stims()
        print("stop stims")
        self.EXIT.set()
        print("exit")
        self.stop_recording() if self.running else ...
        print("stop recording")
        # stop micro controllers
        for interface in self.interfaces.values():
            interface.exit()
        print("stop micros")

        self.shared_buffer.close_all()
        self.shared_buffer.unlink_all()


# TESTING
if __name__ == '__main__':
    # disable chips
    Saver.NEW_FILE_INTERVAL = timedelta(seconds=30)

    class testApp(App):
        SERVER = True
        pass

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

            class RecVars():
                pass
            self.rec_vars = RecVars()
            self.rec_vars.data_length = 3600

            self.root = self
            self.root.ids = RecVars()
            self.root.ids.feedback = RecVars()
            self.root.ids.feedback.text = ''

    EXIT = tr.Event()
    app = testApp()
    tr1 = tr.Thread(target=app.run)
    tr1.start()

    EXIT.wait(timeout=1)

    io = InputOutput(EXIT=EXIT,)

    io.start_recording()
    print('recording started')
    EXIT.wait(timeout=10)
    io.stop_recording()
    print('stopped')
    app.stop()
