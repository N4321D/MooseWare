"""
VERSION 0.1

This script is launched when ever an update file is found

it will use update_client_side.key to decrypt the update file,
next it will be unzipped

finally it will run start.py or start (if executable) from the update file
passing some arguments with information about the setup
"""

from subs.encrypt_aes import Encryption
import os
from zipfile import ZipFile
import json
from shutil import rmtree
from functools import partial
import string
import random

# printing letters
letters = string.ascii_letters + string.digits

UNZIP_DIR = "UPDATE"
UPDATE_PACK_NAME = "MOOSE.update"

class Updater():
    key = None                  # stores the key to decrypt the file
    key_length = 512
    UPDATE_PACK_NAME = UPDATE_PACK_NAME

    def __init__(self, app_version=0) -> None:
        self.e = Encryption()
        self.e.load_private_key("./keys/update_client_side.key")
        self.APPVERSION = app_version

    def decrypt_file(self, file_name):
        self.e.decrypt_file(file_name)

    def update(self, file_name):
        """
        main method to call when update file is detected
        """
        return [action() for action in self._update(file_name)]


    def _update(self, file_name):
        """
        returns a list with all the update actions 
        (this list can be used to iterate throught the actions
        to track the steps, for progress etc)
        """
        actions = []
        
        # decrypt update file
        actions.append(partial(self.decrypt_file, file_name))

        zip_name = os.path.splitext(file_name)[0] + ".dec"
        
        # unzip update file
        _name =  ''.join(random.choice(letters) for i in range(16)) + "/"
        self.unzip_dir = os.path.join(os.path.dirname(file_name), UNZIP_DIR, _name)        
        actions.append(partial(self.unzip, zip_name, self.unzip_dir))

        # remove zip file
        actions.append(partial(os.remove, zip_name))

        # run update script in unzipped dir
        opts = {"app_dir":os.getcwd(),
                "version":self.APPVERSION,
                "unzip_dir": self.unzip_dir
                }
        actions.append(partial(self.install_update, **opts))   # run install script
        actions.append(partial(rmtree, self.unzip_dir))        # remove install files

        return actions

    def install_update(self, **opts):
        """
        this method searches for start_update or start_update.py
        and executes that script with opts as keyword argument
        opts includes app dir, version, unzip dir etc
        """
        runfile = [f for f in os.listdir(self.unzip_dir) if f.startswith("start_update")]
        if len(runfile) == 0:
            raise FileNotFoundError("no update script found")
        runfile = runfile.pop(0)
        
        opts = json.dumps(opts)    # cover opts to json
        
        if runfile.endswith(".py"):
            prefix = "python3 "
        else:
            prefix = ""
        
        _cmd = f"{prefix}{os.path.join(self.unzip_dir + runfile)} -o '{opts}'"
        os.system(_cmd)

    def unzip(self, src, dst):
        with ZipFile(src, "r") as zip:
            zip.extractall(path=dst)
