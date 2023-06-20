"""
Layout of settings panel


[
    {
        "type": "title",
        "title": "Windows"
    },
    {
        "type": "options",
        "title": "Fullscreen",
        "desc": "Set the window in windowed or fullscreen",
        "section": "graphics",
        "key": "fullscreen"
        "options": ["opt1", "opt2", "opt3"]
    }
]


Type        Associated class
-----------------------------
title       SettingTitle
bool        SettingBoolean
numeric     SettingNumeric
options     SettingOptions
string      SettingString
path        SettingPath
timedelta   TimedeltaSettings    # custom class for timedelta objects

"""

import json

_settings_panel = {
"Main": [
    {# guiApp.setupname
    "title": "Setup Name",
        "type": "string",
        "desc": "Name of this Recording Unit",
        "section": "main",
        "key": "setupname",
    },
    {"title": "Display Settings",
        "type": "title",
    },
    {# Screensaver.min_brightness
    "title": "Display Maximal Brightness (%)",
        "type": "numeric",
        "desc": "Maximal brightness of the display (during active use); min: 30%",
        "section": "main",
        "key": "max_brightness",
    },
    {# Screensaver.min_brightness
    "title": "Display Minimal Brightness (%)",
        "type": "numeric",
        "desc": "Minimal brightness of the display (during screensaver)",
        "section": "main",
        "key": "min_brightness",
    },
    {# guiApp.screensaver_timeout
    "title": "Screensaver Timeout",
        "type": "timedelta",
        "desc": "Timeout for the screensaver",
        "section": "main",
        "key": "screensaver_timeout",
    },
],

"Recording": [
    {# SetIO.recording_name
     "title": "Recording Name",
        "type": "string",
        "desc": "Name of the current recording",
        "section": "recording",
        "key": "recording_name",
    },

    # {"title": "Recording Parameters",
    #     "type": "title",
    # },

    {"title": "Save Parameters",
        "type": "title",
    },
    {# guiApp.rec_vars.filename_prefix
     "title": "Filename Prefix",
        "type": "string",
        "desc": "Filename will be: [i][b]prefix[/b][/i]_[i]date[/i]_[i]time[/i].h5",
        "section": "recording",
        "key": "filename_prefix",
    },
    {# guiApp.rec_vars.max_file_size
     "title": "Max File Size",
        "type": "numeric",
        "desc": "Max file size in MBs before splitting the file",
        "section": "recording",
        "key": "max_file_size",
    },
    {# guiApp.rec_vars.hdf_compression
     "title": "Compression Type",
        "type": "options",
        "desc": "Compression Type to use (gzip: better compression, lzf: faster)",
        "section": "recording",
        "key": "hdf_compression",
        "options": ["gzip", "lzf", "None"],
    },
    {# guiApp.rec_vars.hdf_compression_strenght
     "title": "Compression Strenght",
        "type": "options",
        "desc": "Higher is stronger compression",
        "section": "recording",
        "key": "hdf_compression_strenght",
        "options": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
    },
    {# guiApp.rec_vars.hdf_fletcher32
     "title": "HDF use Fletcher32",
        "type": "bool",
        "desc": "Use Fletcher32 checksum to prevent data corruption",
        "section": "recording",
        "key": "hdf_fletcher32",
    },
        {# guiApp.rec_vars.hdf_shuffle
     "title": "HDF use Shuffle Filter",
        "type": "bool",
        "desc": "Use Shuffle filter to improve compression",
        "section": "recording",
        "key": "hdf_shuffle",
    },
    {# guiApp.rec_vars.save_buffer
     "title": "Save Buffer",
        "type": "numeric",
        "desc": "Samples to buffer before saving data (> 2x Recording Rate)",
        "section": "recording",
        "key": "save_buffer",
    }

],
"Other": [
    {"title": "Alerts",
        "type": "title",
    },
    {# settingsScreen.alert_enable
    "title": "SMS Alerts",
        "type": "bool",
        "desc": "Toggle sms alerts",
        "section": "other",
        "key": "alert_enable",
    },
    {# settingsScreen.alert_phone_no
    "title": "Phone Number",
        "type": "string",
        "desc": "Phone number to receive alerts on",
        "section": "other",
        "key": "alert_phone_no",
    },
    {# settingsScreen.alert_phone_no
    "title": "Alert Interval",
        "type": "timedelta",
        "desc": "Interval between SMS alerts",
        "section": "other",
        "key": "alert_interval",
    },
    {# settingsScreen.alert_message
    "title": "Alert Message",
        "type": "string",
        "desc": "Extra information to include in warning message",
        "section": "other",
        "key": "alert_message",
    },
    {"title": "Logging",
        "type": "title",
    },
    {# guiApp.log_level
    "title": "Logging Level",
        "type": "options",
        "desc": "Choose which level of log messages is written to the log file",
        "section": "other",
        "key": "log_level",
        "options": ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    },
],

}


settings_panel = {k: json.dumps(v) for k, v in _settings_panel.items()}   # k: Panel name, v: panel json
del _settings_panel

# TODO: Logger Parameter section