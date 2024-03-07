import platform
import subprocess
import json
import time
import asyncio
import threading

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



class AutoMounter:
    MOUNTABLE_FSTYPES = {"ext4", "vfat", "ntfs", "exfat"}

    def __init__(self, dt=1) -> None:
        self.usb_drives = {}        # all usb drives
        self.mounted_drives = {}    # mounted drives

        self.CHECK_TIMEOUT = dt     # timeout for check loop
        self.PMOUNT_INSTALLED = False

        try:
            subprocess.run("pmount")
            if platform.machine() in {"armv7l", "aarch64"}:
                self.PMOUNT_INSTALLED = True
                log("Pmount installed", "debug")

        except FileNotFoundError:
            if platform.machine() in {"armv7l", "aarch64"}:
                # Raspberry pi, but pmount not installed
                log(
                    "Pmount not installed, install with 'sudo apt install pmount'",
                    "warning",
                )

    def parse_lsblk(
        self,
        columns=[],
        unpack_partitions=True,
    ) -> dict:
        """
        parses lsblk info as json object

        Args:
            columns (list, optional): columns to return from lsblk see info
                                      below for desription
            unpack_partitions (bool): if partitions should be unpacked or not
                                      (if not partitions are items under the
                                       key 'children' under the root dev)

        Returns:
            dict: dictionary with lsblk info. Key is the first column in columns
                  or the name, value is the rest of the information

        Available output columns:
        NAME            device name
        KNAME           internal kernel device name
        PATH            path to the device node
        MAJ:MIN         major:minor device number
        FSAVAIL         filesystem size available
        FSSIZE          filesystem size
        FSTYPE          filesystem type
        FSUSED          filesystem size used
        FSUSE%          filesystem use percentage
        FSROOTS         mounted filesystem roots
        FSVER           filesystem version
        MOUNTPOINT      where the device is mounted
        MOUNTPOINTS     all locations where device is mounted
        LABEL           filesystem LABEL
        UUID            filesystem UUID
        PTUUID          partition table identifier (usually UUID)
        PTTYPE          partition table type
        PARTTYPE        partition type code or UUID
        PARTTYPENAME    partition type name
        PARTLABEL       partition LABEL
        PARTUUID        partition UUID
        PARTFLAGS       partition flags
        RA              read-ahead of the device
        RO              read-only device
        RM              removable device
        HOTPLUG         removable or hotplug device (usb, pcmcia, ...)
        MODEL           device identifier
        SERIAL          disk serial number
        SIZE            size of the device
        STATE           state of the device
        OWNER           user name
        GROUP           group name
        MODE            device node permissions
        ALIGNMENT       alignment offset
        MIN-IO          minimum I/O size
        OPT-IO          optimal I/O size
        PHY-SEC         physical sector size
        LOG-SEC         logical sector size
        ROTA            rotational device
        SCHED           I/O scheduler name
        RQ-SIZE         request queue size
        TYPE            device type
        DISC-ALN        discard alignment offset
        DISC-GRAN       discard granularity
        DISC-MAX        discard max bytes
        DISC-ZERO       discard zeroes data
        WSAME           write same max bytes
        WWN             unique storage identifier
        RAND            adds randomness
        PKNAME          internal parent kernel device name
        HCTL            Host:Channel:Target:Lun for SCSI
        TRAN            device transport type
        SUBSYSTEMS      de-duplicated chain of subsystems
        REV             device revision
        VENDOR          device vendor
        ZONED           zone model
        DAX             dax-capable device
        """
        columns = [i.upper() for i in columns]  # covert to upper case
        args = ["lsblk", "--json"]

        if columns:
            args.append("-o" + ",".join(columns))

        lsblk_out = subprocess.run(args, capture_output=True).stdout

        if not lsblk_out:
            return {}

        lsblk_out = json.loads(lsblk_out).get("blockdevices", [])

        if unpack_partitions:
            lsblk_out += [
                partition
                for dev in lsblk_out
                for partition in dev.get("children", [])
                if partition
            ]

        key = columns[0] if columns else "NAME"  # set key to first item in columns
        output = {i[key.lower()]: i for i in lsblk_out}  # convert to dict
        return output

    def check_mounted(self):
        self.usb_drives = self.parse_lsblk(
            [
                "PATH",
                "FSTYPE",
                "SIZE",
                "HOTPLUG",
                "NAME",
                "MOUNTPOINT",
                "LABEL",
                "SUBSYSTEMS",
            ],
            unpack_partitions=True,
        )

        # mount drives
        for dev, info in self.usb_drives.items():
            if (
                info["hotplug"]
                and info["fstype"] in self.MOUNTABLE_FSTYPES
                and "usb" in info["subsystems"]
            ):  # select only usb and removable devices
                if info["mountpoint"] is None:  # mount drive
                    self.mount_drive(dev, info["label"])
                    self.mounted_drives[dev] = info

                else:
                    # add already mounted drives
                    self.mounted_drives[dev] = info

        # unmount drives that are not connected anymore
        for disconnected_dev in set(self.mounted_drives).difference(self.usb_drives):
            self.unmount_drive(disconnected_dev)
            del self.mounted_drives[disconnected_dev]

    def mount_drive(self, dev, label=None):
        log(f"mounting {dev}", "debug")
        if not self.PMOUNT_INSTALLED:
            return
        args = ["pmount", 
                "--umask", "000", 
                "--noatime", 
                "-w", 
                "--sync", 
                dev
                ]
        if label:
            args.append(label)

        res = subprocess.run(args)
        if res.returncode != 0:
            log(f"Error mounting {dev}: {res.stderr}", "warning")

    def unmount_drive(self, dev):
        log(f"unmounting {dev}", "debug")
        if not self.PMOUNT_INSTALLED:
            return
        res = subprocess.run(["pumount", dev])
        if res.returncode != 0:
            log(f"Error unmounting {dev}: {res.stderr}", "warning")

    async def check_mounted_async(self):
        while True:
            print('check async')
            self.check_mounted()
            await asyncio.sleep(self.CHECK_TIMEOUT)

    def check_mounted_thread(self):
        while True:
            print('check tr')
            self.check_mounted()
            time.sleep(self.CHECK_TIMEOUT)

    def start(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.check_mounted_async())
            else:
                raise RuntimeError("No running event loop")
            
        except RuntimeError:
            self._checking_thread = threading.Thread(
                target=self.check_mounted_thread, daemon=True
            )
            self._checking_thread.start()


if __name__ == "__main__":
    print("Automounter test, automounter initiated as 'm'")
    m = AutoMounter()
    m.start()
