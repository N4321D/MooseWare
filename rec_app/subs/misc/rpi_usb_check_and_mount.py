from pathlib import Path
import platform
import os
import json

try:
    # Setup logging
    from subs.log import create_logger

    logger = create_logger()

    def log(message, level="info"):
        getattr(logger, level)(
            f"AUTOMOUNT: {message}"
        )  # change RECORDER SAVER IN CLASS NAME

except:

    def log(*args):
        print("AUTOMOUNT: ", *args)


class AutoMounter:
    usb_drives = {}
    mounted_drives = {}
    disconnected_drives = {}

    MOUNTABLE_FSTYPES = {"ext4", "vfat", "ntfs", "exfat"}

    def __init__(self) -> None:
        if (not os.popen("pmount").read(0)) and (
            platform.system() in {"armv7l", "aarch64"}
        ):
            # Raspberry pi, but raspbian not installed
            log("Pmount not installed, install with sudo apt install pmount", "warning")

    def parse_lsblk(
        self,
        columns=["PATH", "FSTYPE", "SIZE", "MOUNTPOINT", "NAME", "HOTPLUG"],
        unpack_partitions=True,
    ):
        """
        parses lsblk info as json object

        Args:
            COLUMNS (list, optional): columns to return from lsblk see info 
                                      below for desription
            unpack_partitions (bool): if partitions should be unpacked or not 
                                      (if not partitions are items under the 
                                       key 'children' under the root dev)

        Returns:
            _type_: _description_

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
        lsblk_out = json.loads(
            os.popen(
                f"lsblk --json {('-o' + ','.join(columns)) if columns else ''}"
            ).read()
        ).get("blockdevices", [])

        if unpack_partitions:
            lsblk_out += [
                partition for dev in lsblk_out 
                for partition in dev.get("children", []) 
                if partition
            ]

        key = columns[0] if columns else "NAME"  # set key to first item in columns
        output = {i[key.lower()]: i for i in lsblk_out}  # convert to dict
        return output

    def check_mounted(self):
        self.usb_drives = self.parse_lsblk(
            ["PATH", "FSTYPE", "SIZE", "HOTPLUG", "NAME", "MOUNTPOINT", "LABEL"],
            unpack_partitions=True,
        )

        # mount drives
        for dev, info in self.usb_drives.items():
            if info["hotplug"] and (
                info["fstype"] in self.MOUNTABLE_FSTYPES
            ):  # select only usb and removable devices
                if info["mountpoint"] is None:  # mount drive
                    self.mount_drive(dev)
                    self.mounted_drives[dev] = info

                else:
                    # add already mounted drives
                    self.mounted_drives[dev] = info

        # unmount drives that are not connected anymore
        for disconnected_dev in set(self.mounted_drives).difference(self.usb_drives):
            self.unmount_drive(disconnected_dev)
            del self.mounted_drives[disconnected_dev]

    def mount_drive(self, dev):
        log(f"mounted {dev}", "debug")

        # os.popen(f"pmount ... {dev}")
        # TODO mount here

    def unmount_drive(self, dev):
        log(f"unmounted {dev}", "debug")
        # os.popen(f"pumount ... {dev}")
        # TODO unmount here


if __name__ == "__main__":
    print("Automounter test, automounter initiated as 'm'")
    m = AutoMounter()
