"""

This function tests SSL key and returns if it is expired or not
(TRUE/FALSE)  and the key

This is used to check if the license is valid

Also: 
The serial/MAC address of the device is checked and written to 
an encrypted file. This binds the setup to that device


"""
try:
    from subs.log import create_logger
except:
    def create_logger():
        class Logger():
            def __init__(self) -> None: 
                f = lambda *x: print("VERIFY LICENSE: ", *x)  # change messenger in whatever script you are importing
                self.warning = self.info = self.critical = self.debug = self.error = f
        return Logger()

logger = create_logger()

def log(message, level="info"):
    getattr(logger, level)("VERIFY LICENSE: {}".format(message))  # change RECORDER SAVER IN CLASS NAME


import uuid

from cryptography.fernet import Fernet
from subs.encrypt_aes import Encryption

MACADDRESS = (':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                        for ele in range(0, 8 * 6, 8)][::-1])) 
UNIQUE_ID = uuid.uuid3(uuid.NAMESPACE_OID, str(uuid.getnode()))
SER_KEY = b'MJS1L_7vLsqJssXzBihoTPtQ4-tRlZiA0JiiXU7eUPA='  # key for serial file
KEY_PATH = "./keys/"

def check_serial():
    """
    This function opens the serial no file and checks if the saved 
    serial matches the cpu id or macaddress
    If the serial has a specific pattern, the hardware id is saved to the serial file 
    (for first boot)
    after that the app is bound to the serial/mac address which was saved.
    """
    fernet = Fernet(SER_KEY)
    hardware_serial = get_serial()
    with open(KEY_PATH + "serialno.moose", "rb") as file:
        txt = file.readlines()
        serial = fernet.decrypt(txt[5])[len("SERIAL = "):]

    if serial == b'THE_MOOSE_IS_GREAT_!!!_XC4QmTy8_rRgw_2quwPqqC081biip0vq3sS5ULG-qkI=':
        # no serial no saved (first boot), save serial
        with open(KEY_PATH + "serialno.moose", "wb") as file:
            txt[5] = fernet.encrypt(f"SERIAL = {hardware_serial}".encode())
            file.writelines(txt)
            log("new serial saved", "info")
            return "new"
    else:
        # check if serial matches
        if serial != hardware_serial.encode():
            log("Hardware ID of setup ({}) does not match license ({})".format(hardware_serial, serial.decode()), "critical")
            raise ValueError("Serial does not match hardware id")

        else:
            log("Serial OK", "info")
            return "ok"

# get serial for RPIs:
def get_serial():
    # Extract serial from cpuinfo file
    serial = MACADDRESS
    try:
        with open('/proc/cpuinfo', 'r') as file:
            for l in file:
                if l[0:6] == 'Serial':
                    serial = l[10:26]

    except FileNotFoundError:
        # WINDOWS OR MAC
        pass
    log(f"serial no.: {serial}", "debug")
    return serial

if __name__ == "__main__":
    def log(msg, level):
        print("[{}]:".format(level.upper()), "[VERIFICATION]", msg)

    key = KEY_PATH + "client.pem"
    cert = KEY_PATH + "ca.cer"
    e = Encryption()
    e.load_all(key, cert)
    print(e.check_certificates())

# TODO VALIDATE KEY BEFORE GETTING END DATE
