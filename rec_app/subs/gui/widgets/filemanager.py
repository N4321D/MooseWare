"""
Filemanager widget for kivy

checks for connected usb drives on linux systems

can copy, move, delete files

limit access upper folder by setting
Filemanager.filechooser.rootpath after init

set current folder by settings
Filemanager.filechooser.path after init

Filemanager.main_loop_event can be called or stopped on entering or exiting
the screen to which filemanager is added to start or stop automatic
refresh etc
"""

import psutil
from functools import partial
import shutil
from pathlib import Path

import os
import platform
import time

from subs.gui.vars import WHITE, MO, BUT_BGR, MO_BGR
from subs.gui.buttons.DropDownB import DropDownB
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.app import App
from subs.gui.vars import BUT_BGR, MO, MO_BGR

import concurrent.futures

# create logger
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None:
                # change messenger in whatever script you are importing
                f = lambda *x: print("FILEMANAGER: ", *x)
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()


def log(message, level="info"):
    # change RECORDER SAVER IN CLASS NAME
    getattr(logger, level)("FILEMANAGER: {}".format(message))


Builder.load_string(
    """
<FM_Button>:
    size_hint: (0.2, 0.1)

<FileManager>:
    FileChooserIconView:
        id: filechooser
        size_hint: (0.8, 0.9)
        pos_hint: {"x": 0, "y": 0.1}
        path: root.path
        rootpath: root.rootpath
        multiselect: True
        dirselect: True

    # copy button
    FM_Button:
        id: copybut
        text: "Copy"
        pos_hint: {"x": 0.8, "y": 0.2}
        disabled: True if dstbut.text == "Destination" else False
        on_release:
            _dst = root.connected_usb.get(dstbut.text)
            _dst = _dst.get("mountpoint") if _dst is not None else None
            root.copy_del(filechooser.selection, "Copy", dst=_dst)

    # delete button
    FM_Button:
        id: delbut
        text: "Delete"
        pos_hint: {"x": 0.8, "y": 0}
        # dont use partial -> cannot erase selection then
        on_release: root.copy_del(filechooser.selection, "Delete")

    # view USB Button
    FM_Button:
        id: viewusbbut
        text: "View USB"
        disabled: True if dstbut.text == "Destination" else False
        pos_hint: {"x": 0.8, "y": 0.4}
        on_release: root.switch_view()

    # destination button
    FM_DropDownB:
        id: dstbut
        text: "Destination"
        pos_hint: {"x": 0.8, "y": 0.3}
        size_hint: 0.2, 0.1
        types: ["NO USB FOUND"]
        on_release:
            root.check_usb_drives()

    # no. selected label
    Label:
        id: sel_lbl
        text: ""
        size_hint: (0.2, 0.1)
        pos_hint: {"x": 0.8, "y": 0.1}
        markup: True

    # feedback label
    Label:
        id: fb_lbl
        text: "Ready..."
        size_hint: (0.2, 0.3)
        pos_hint: {"x": 0.8, "y": 0.5}
        markup: True
        text_size: self.size

    # Remaining Label
    Label:
        id: rem_lbl
        text: "Remaining"
        size_hint: (0.2, 0.2)
        pos_hint: {"x": 0.8, "y": 0.8}
        markup: True
        valign: "top"
        halign: "right"
        text_size: self.size
"""
)


def sec_2_t_passed(sec):
    """
    This function takes seconds as input and returns how
    many days, hours, min, seconds have passed
    """
    days, sec = divmod(sec, 86400) if sec >= 86400 else (0, sec)
    hours, sec = divmod(sec, 3600) if sec >= 3600 else (0, sec)
    mins, secs = divmod(sec, 60)
    return days, hours, mins, secs

def convert_bytes(num_bytes):
    units = [("TB", 1e12), ("GB", 1e9), ("MB", 1e6), ("KB", 1e3), ("bytes", 0)]
    for unit, value in units:
        if num_bytes >= value:
            quotient = num_bytes / value
            return f"{quotient:.2f} {unit}" if quotient < 100 else f"{quotient:.0f} {unit}"


def check_disk_space(directory, bitrate=float("NaN"), warning=None,
                     t_warning=None, error=None, t_error=None,
                     spare=1024e6, spare_t=3600):
    """
    Calculates the remaining disk space and recording time based on the given bitrate,
    and returns a dictionary indicating the disk space and recording time status.

    Parameters:
    directory (str): The directory for which disk space and recording time should be calculated.
    bitrate (float, optional): The bitrate of the recording. Default is `float("NaN")`.
    warning (int, optional): The disk space threshold for returning a warning.
    t_warning (int, optional): The recording time threshold for returning a warning.
    error (int, optional): The disk space threshold for returning an error.
    t_error (int, optional): The recording time threshold for returning an error.
    spare (int, optional): The spare disk space to keep for safety. Default is `1024e6`.
    spare_t (int, optional): The spare recording time to keep for safety. Default is `3600`.

    Returns:
    dict: A dictionary containing the following keys:
        diskspace (dict): A dictionary with the keys `space` and `status` indicating the
            remaining disk space and its status respectively.
        rem_t (dict): A dictionary with the keys `t` and `status` indicating the
            remaining recording time and its status respectively.
        stop (bool): A boolean indicating whether the recording should stop due to low disk space.
    """

    space = psutil.disk_usage(directory).free
    # remaining rec time in sec (/8 -> bits to Bytes)
    time_remain = space/bitrate/8

    # extra space:
    time_remain -= spare_t              # always have 1h extra
    space -= spare                      # always leave 1 extra GB spare space

    # convert space:
    if space <= error:
        space_status = "error"
    elif space <= warning:
        space_status = "warning"
    else:
        space_status = 'ok'

    # Time
    if time_remain <= t_error:
        t_status = "error"
    elif time_remain <= t_warning:
        t_status = 'warning'
    else:
        t_status = "ok"

    return {"diskspace": {"space": space, "status": space_status},
            "rem_t": {"t": time_remain, "status": t_status},
            "stop": space == 1}

def copy_file(src, dst, overwrite=True, make_parents=True, 
              mode=0o777,
              force_copy2=False,
              check_done=True):
    """
    Copy a file from one location to another. Uses os.sendfile whereever possible

    Arguments:
    src -- str or pathlib.Path, source file path or Path object
    dst -- str or pathlib.Path, destination file path or Path object
    overwrite -- bool, optional, overwrite the destination file if it already exists, defaults to True
    make_parents -- bool, optional, create parent directories of the destination file if they don't exist, defaults to True
    mode -- int, optional, permission for files
    force_copy2 -- bool, optional, force use of copy2 instead of os.sendfile
    check_done -- bool, optional, blocks until filesize of src == filesize of dst (to prevent data loss)

    Raises:
    FileExistsError -- If the destination file already exists and overwrite is set to False
    """

    if not isinstance(src, Path):
        src = Path(src) 
    if not isinstance(dst, Path):
        dst = Path(dst)
    
    # over write:
    if dst.exists() and not overwrite:
        raise FileExistsError("Destination file already exists")
    
    if overwrite:
        dst.unlink(missing_ok=True)
    
    # Make parent dirs
    if make_parents:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            dst.parent.chmod(mode)
            
        except Exception as e:
            log(f"Cannot change dir priveliges: {e}", "warning")

    # Copy:
    if (platform.system() == 'Windows') or force_copy2:
        shutil.copy2(src, dst)
    else:
        with src.open('rb') as src_f, dst.open('wb') as dst_f:
            os.sendfile(dst_f.fileno(), src_f.fileno(), 0, src.stat().st_size)
    
    # set permissions:
    dst.chmod(mode)

    # wait until copying is done: src.size == dst.size
    if check_done:
        src_size = src.stat().st_size
        while src_size != dst.stat().st_size:
            time.sleep(0.1)


class FM_Button(Button):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_size = '15sp'
        self.color = MO
        self.background_color = BUT_BGR
        self.halign = "center"
        self.valign = "center"
        self.markup = True


class FM_DropDownB(DropDownB):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.font_size = '15sp'
        self.color = WHITE
        self.background_color = MO_BGR
        self.drop_but_size = "50sp"

class Action():
    """
    An action to run with a given function and text.

    Attributes:
    f (function): The function to run.
    text (str): The text to show in the progress bar.

    """
    __slots__ = ('f', 'text')
    def __init__(self, f, text="") -> None:
        """
        Initialize the Action instance.

        Args:
            f (function): The function to run.
            text (str, optional): The text to show in the progress bar. Defaults to an empty string.

        """
        self.f = f              # function to run
        self.text = text        # text to show in pbar
    
    def run(self, progress, main_text):
        """
        run f
        - progress: progress bar item
        - main_text: main action such as copying etc

        """
        if not hasattr(progress, "running_items"):
            progress.running_items = []
        if self.text:
            # add item to text
            progress.running_items.append(self.text)
            progress.children[2].text = main_text + "\n" + "\n".join(progress.running_items)
        
        # run 
        out = self.f()
        
        if self.text:
            # remove item from text
            progress.running_items.remove(self.text)
            progress.children[2].text = main_text + "\n" + "\n".join(progress.running_items)
        return out


def confirmation(cls, txt, action):
    """
    displays text and yes or no as options
    if yes is chosen, action will be launched,
    if no, nothing will be done

    overwrite this with a popup class or buttons to use in script
    Yes button must launch action
    """
    print(txt)
    return action()


class FileManager(FloatLayout):
    MAX_PARALLEL_OPS = 3        # maximum number of parallel file ops
    connected_usb = {}
    last_listdir = set()           # set with files since last update
    progress = None             # progress bar placeholder
    path = "."
    rootpath = "."
    # indicates cancelation of pb action after pressing cancel
    confirmation = confirmation
    # folders/files/extension to exclude from copy (extension must start with . e.g. .h5)
    exclude = {".vscode", "__pycache__"}

    space_pars = {"bitrate": float('NaN'),              # bitrate for recordings used to calculate space remaining
                  # warning level for space in bytes (1024e6=1GB)
                  "warning": 1e6,
                  "error": 0.5e6,               # error level for space
                  "t_warning": 24*3600,         # warning level for remaining time in sec
                  "t_error": 6*3600,            # error level for remaining time in sec
                  # extra disk space (not included in calculation)
                  "spare": 1e6,
                  # extra time (not included in calculation)
                  "spare_t": 3600,
                  }
    # can be changed when calling an instance
    UPDATE_NAME = "MOOSE.update"

    # concurrent processing vars
    futures = []                                # list with futures running in executor
    executor = None

    def __init__(self, setupname=None, name=None, client=None,
                 **kwargs) -> None:
        """
        feedback is a function that prints or logs its args
        name is a name of the setup or system..
        """
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.setupname = self.app.setupname
        self.client = client

        # init widgets on start
        Clock.schedule_once(self.__kv_init__, 0)

        # launch main loop
        self.main_loop_event = Clock.schedule_interval(self.main_loop, 1)
    
    def __kv_init__(self, dt):
        self._init_widgets()


    def update_func(_x): 
        """
        placeholder for called update function if update file is found
        """
        return _x


    def _init_widgets(self, *args):
        """
        This is laumched when kivy app starts
        Inits widgets and links properties
        """
        # link all widgets as self properties
        [setattr(self, wid, self.ids[wid]) for wid in self.ids]

        # update label with changing selection:
        self.filechooser.bind(selection=lambda *x: setattr(self.sel_lbl,
                                                           "text",
                                                           "Selected: {}".format(len(self.filechooser.selection))))

    def main_loop(self, *args):
        """
        is launch on init and checks files every x seconds
        """
        if self.tasks_running() is True:
            return

        self.update_file_list()

        try:
            self.check_space()

        except OSError as e:
            log(e, "warning")

        self.check_usb_drives()

    def tasks_running(self):
        """
        Checks if any operations are running and updates the progress bar if necessary.

        Returns:
        bool: True if any tasks are still running, False otherwise.

        Notes:
        - The function uses the `concurrent.futures.wait` method to check the status of the tasks in `self.futures`.
        - If there are no tasks running, the function returns False and performs cleanup by calling the `stop_tasks` method.
        """
        # test if any operations are running
        done = concurrent.futures.wait(self.futures, timeout=0)
        if not done.done and not done.not_done:
            # nothing running
            return False

        # update progress bar
        if self.progress:
            self.progress.index = len(done.done)

        if not done.not_done:
            # all done, do cleanup
            # exctract results:
            result = []
            for task in done.done:
                try:
                    _res = task.result()
                
                except Exception as e:
                    log(e, "warning")
                    _res = e

                if _res:
                    result.append(str(_res))

            if not result:
                result = ['Done']
            
            self.stop_tasks(result, cancel=True)        # stop executor
            self.update_file_list()                     # force update view
            return False

        else:
            # still running
            return True
        

    def check_usb_drives(self, *args):
        self.connected_usb = self.check_connected_drives()
        self.dstbut.types = list(self.connected_usb)
        if self.dstbut.text not in self.dstbut.types:
            self.dstbut.text = "Destination"

    def check_space(self):
        """
        Checks the available disk space for the specified disk(s) and updates the GUI with the results.

        The function uses the `check_disk_space` function to get the disk space information and maps the
        space status to a color using the `pallette` dictionary. The disk space information is then
        formatted and stored in the `_txt` dictionary, which is then used to update the GUI with the
        disk space information.
        """

        disks = {"HDD": self.path}
        disks.update({name.split(':')[0]: usb['mountpoint']
                      for name, usb in self.connected_usb.items()})

        _txt = {}
        pallette = {"ok": "", "warning": "#FFFF00", "error": "#FF0000"}

        for d in disks:
            space = check_disk_space(disks[d], **self.space_pars)
            color = pallette[space["diskspace"]["status"]]

            _txt[d] = (
                f"[b][color={color}]{convert_bytes(space['diskspace']['space'])}[/color][/b]")

        self.rem_lbl.text = "Free Space:\n" + \
            "\n".join([f"{v} {k: >4} " for k, v in _txt.items()]) + "\n"

    def update_file_list(self):
        """
        Update the file list in the filechooser widget if the directory has changed.

        This function checks if the current directory has changed compared to the last
        directory and updates the file list in the filechooser widget only if it has changed.
        If the directory cannot be found, the function logs the error and returns.
        """
        _dir = Path(self.filechooser.path)
        
        try:
            l_dir = set(_dir.iterdir())
            
        except:
            self.last_listdir = set()
            self.filechooser._update_files()
            return

        if self.last_listdir != l_dir:
            self.last_listdir = l_dir
            self.filechooser._update_files()
    
    def stop_tasks(self, result=[], cancel=False):
        # show output, errors etc
        if result:
            self.fb_lbl.text = "\n".join(result)
            if len(self.fb_lbl.text) > 200:
                self.fb_lbl.text = f"[size=10sp]{self.fb_lbl.text}[/size]"
        else:
            self.fb_lbl.text = "Ready"

        if not cancel:
            self.filechooser.selection = []
        self.executor = self.executor.shutdown(wait=not cancel, cancel_futures=cancel)
        self.futures = []
        self._hide_pb()             # hide progress bar when finished with action

    def cancel(self, *args):
        """
        cancel action that is running with progress bar
        """
        self.progress.children[2].text = "Cancelling... Please Wait"
        self.progress.children[0].children[0].disabled = True
        return Clock.schedule_once(lambda *_: self.stop_tasks(cancel=True), 0)

    def do_with_pb(self, action_list, text="Progress",):
        """
        Executes a list of functions in a separate thread with a progress bar display.

        Args:
        - action_list (List[Callable]): A list of functions to be executed by the executor.
        - text (str, optional): The text to be displayed on the progress bar. Default is "Progress".

        Returns:
        None

        Notes:
        - the callables in the action list must be the f of the Action class
        - Action.text will be displayed on the progress bar as running action
        - The progress bar is implemented using the `concurrent.futures.ThreadPoolExecutor` class.
        - The progress bar displays the progress of each task and the overall progress of all tasks.
        """
        # TODO use asyncio here instead of threading
        self.progress = self.filechooser.progress_cls()
        self.progress.value = 0
        self.add_widget(self.progress)

        self.progress.children[2].text = text
        
        # cancel button
        self.progress.children[0].children[0].color = WHITE
        self.progress.children[0].children[0].background_color = MO_BGR
        # other progress options
        self.progress.total = len(action_list)

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_PARALLEL_OPS)
        self.futures = [self.executor.submit(action.run, self.progress, text) 
                        for action in action_list]
    

    def copy_del(self, file_list, operation:str, dst=None, confirmation=False):
        """
        Copies or deletes files

        Args:
            file_list (list): List of files/directories to be copied or deleted.
            operation (str): 'Copy' or 'Delete', indicates the action to be performed on the files.
            dst (str, optional): Destination directory to copy the files to. Default is None.
            confirmation (bool, optional): Boolean flag to indicate if confirmation is required before performing the action. Default is False.

        Returns:
            None
        """
        if dst:
            dst = Path(dst)

        if not confirmation:
            # Create Confirmation popup with current action:
            
            _i_dirs = False if operation == "Delete" else True
            
            selection = set(file_list) - set(self.filechooser.path)  # remove current path if included

            # recursively add all items in subfolders, exclude items with match exclusion
            file_list = sum(map(lambda x: self.proc_selected_item(x, _i_dirs), selection), [])  # sum concatenates lists
            
            txt = (f"Are you sure you want to {operation}\n"
                   f"{len(selection)} items")
            if _i_dirs:                
                txt += f" {len(file_list)} files)"

            action = partial(self.copy_del, file_list,
                             operation, dst, confirmation=True)

            return self.confirmation(txt, action)

        if not file_list:
            self.fb_lbl.text = "Nothing Selected"
            return

        action_list, txt = [], f"{operation} Please Wait..."
        self.fb_lbl.text = f"{operation}...\nPlease Wait"

        if operation == 'Delete':
            def act(src):
                try:
                    if src.is_dir():
                        shutil.rmtree(src)
                    else:
                        src.unlink(missing_ok=True)

                except Exception as e:
                    raise e
                
                # wait untill deleted
                while src.exists():
                    time.sleep(0.3)

            action_list = [Action(partial(act, src),
                                  text=src.name) 
                            for src in file_list]
            txt = "Deleting:"

        elif operation == 'Copy':
            if not (dst or dst.is_dir()):
                self.fb_lbl.text = f"Target Drive:\n[b]{dst.name}[/b]\nnot found"
                return

            else:
                dst = (dst
                       / "RECORDED_DATA"
                       / f"{self.setupname or ''}"
                       )

            def act(src, dst, err=None):
                # add destination subfolders
                dst /= src.relative_to(Path(self.rootpath).absolute())
                copy_file(src, dst)
                return str(err) if err else ""

            action_list = [Action(partial(act, src, dst),
                    text=f"{src.name}{convert_bytes(src.stat().st_size): >10}")
                    for src in file_list if (not src.is_dir() and src.exists())
                    ]

            txt = "Parallel Copying:"

        self.do_with_pb(action_list, txt)

    def switch_view(self, *args):
        """
        Switches the view of the filemananger to the selected usb drive
        """
        self.filechooser.selection = []
        if self.filechooser.rootpath == self.rootpath:
            try:
                self.filechooser.rootpath = self.connected_usb[self.dstbut.text]["mountpoint"]
                self.filechooser.path = self.connected_usb[self.dstbut.text]["mountpoint"]
                self.copybut.disabled = True
                self.viewusbbut.text = "View HDD"

                # update if update file found on usb root
                update_loc = Path(self.filechooser.path) / self.UPDATE_NAME
                if update_loc.exists():
                    self.confirmation("Update System?", partial(
                        self.run_update, update_loc))

            except KeyError as e:
                log(e, level="debug")
        else:
            self.filechooser.rootpath = self.rootpath
            self.filechooser.path = self.path
            self.copybut.disabled = False
            self.viewusbbut.text = "View USB"
        
        self.update_file_list()

    def run_update(self, update_loc, *args):
        self.fb_lbl.text = "Updating..."
        try:
            log("Updating", "info")
            _actions = self.update_func(update_loc)
            _actions.append(partial(setattr, self.fb_lbl,
                            "text", "Update Successful"))
            self.do_with_pb(_actions,
                            text="Installing Update...")
            log("Update Successful", "info")

        except Exception as e:
            log(f"Cannot Update: {e}", "error")
            self.fb_lbl.text = f"Update Failed: {e}"

        return

    # MISC METHODS
    def _hide_pb(self):
        # hide progress bar
        if self.progress:
            self.remove_widget(self.progress)
            self.progress = None
    
    def proc_selected_item(self, item, iter_dir=False):
        """
        Process the selected item, including any child items if it is a directory.
        Returns a list of Path objects, excluding any parts specified in `self.exclude`.
        
        Parameters:
        item (str): The selected item to process.
        iter_dir (bool): if true walk through (sub)directory items to find individual files
        
        Returns:
        list: A list of Path objects that are processed and filtered.
        
        """
        out = [Path(item)]
        if out[0].is_dir() and iter_dir:
            out.extend(out[0].glob("**/*"))
        return [p for p in out if not self.exclude.intersection(p.parts)]


    @staticmethod
    def check_connected_drives(*_) -> dict:
        """
        This function checks for connected drives, such as USB drives, 
        and returns their information as a dictionary.
        
        Returns:
        dict: A dictionary containing the name, type, and usage information of connected drives.
        """
        drives = {}

        usb_i = 0
        for part in psutil.disk_partitions():
            if ({'removable', 'usb'}.intersection(part.opts)   # general win, linux
                or part.fstype == ""   # OSX
                or "/media/" in part.mountpoint   # RPI
                ):
                drive = part._asdict()
                try:
                    drive.update(
                        {'usage': psutil.disk_usage(part.mountpoint)._asdict()})
                    drive['name'] = f"USB{usb_i}: {convert_bytes(drive['usage']['total'])}"
                    usb_i += 1
                    drives[drive['name']] = drive
      
                except PermissionError:
                    # needed for Windows
                    pass

        return drives


# TODO: improve check connected drive, look for more specific way to detect usb?

if __name__ == "__main__":
    class MyApp(App):
        setupname = "test_setup"

        def build(self):
            return FileManager()

    app = MyApp()
    app.run()
    print("use fm = app.root to access filemanager as fm")
