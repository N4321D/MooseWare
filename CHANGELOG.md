# Changelog

09 Feb 2023:
- Filemanager:
    - improved with pathlib
    - check if copy or deleted completed
    - parallel file ops
- Fixed pressure sens not working
- added central clock (in root widget):
    - click on it to change all times to utc time
    - changed graphs to plot in utc time if utc bool is true
    - notes change to utc if in utc

21 Feb. 2022:
- Shared memory for recording and plotting
- New file structure: data is saved as np structured array
- Notes are structured array

21 October 2021:
- Autostim: stop awake nudge when pressing stop

10 October 2021:
- Autostim:
    - Keep awake function added
    - Forced thresholding added
- Messenger: Created Kivy overlay so that configparser properties can be loaded


06 October 2021:
- GPIO:
    - added GPIO out
- All sensors: fixed settings being shared (by copying self.defaults on init)
- Fixed green led intensity not saved 
- Notes:
    - Fixed black box when text is bigger than texture


01 October 2021
- Motion Sensor:
    - change sensitivity
- All Sensors:
    - settings panel
- Settings:
    - scrollable options popup
    - wifi in settings
    - time zone in settings
- Notes
    - do not add when already open
    - linked to root widget

01 April 2021:
- Autostim:
    - tested and working

- MainApp:
    - finished settings panel

27 March 2021:
- Autostim:
    - create settings panel
    - created tracking panel
    - still needs testing to verify if it works
- MainApp:
    - started on config and settings panel

16 March 2021:
- Filemanager:
    - improved copy function & delete function
    - introduced error reporting of copy/del
    - usb detection with mount (works on osx/linux)
- Rec Screen:
    - added widget panel for sensors
    - sensor status responds live to status of sensor
    - Improved OIS driver (includes stim now)
- Setings and I/O:
    - track status of sensors
    - improved detection of connected sensors

11 March 2021:
-   autostim under construction
-   improved byte to int conversion in chip drivers
