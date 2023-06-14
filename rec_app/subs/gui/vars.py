from datetime import timedelta

# PARS:
MAX_MEM = 128e6                     # max mem to use for buffers in Bytes

# COLORS (R, G, B, A):
BACKBLACK = (0, 0.01, 0.07, 1)
BLUE = (0.06, 0.6, 0.97, 1)
LIGHTER_BLUE = (0, 0, 0.3, 1)       # for text using markup (convert to rgba code)
BUT_BGR = (0.265, 0.351, 0.394, 1)   #(0.365, 0.451, 0.494, 0.9) 
GRAPH_AX = (1, 1, 1, 1)
GRAPH_BACKGROUND = (0.1, 0.1, 0.1, 0.9)
GREEN_BRIGHT = (0.15294, 0.98431, 0.41960, 1)

GREEN_OK = (0, 1, 0, 0.6)
GREY = (0.365, 0.451, 0.494, 1)
MINUS_RED = (0.63529, 0.28627, 0.21176, 1)
RED = (1, 0, 0, 0.5)
MO = (0.8, 0.3, 0, 1)
MO_BGR = (1, 0.5, 0.2, 1)
PLUS_GREEN = (0.24313, 0.33725, 0.25490, 1)
SLIDER_ORANGE = (0.8, 0.3, 0, 0.5)
WHITE = (1, 1, 1, 1)
YELLOW = (0.90980, 0.77254, 0.27843, 1)

# CHIP_WIDGETS
CW_BUT_BGR_DIS = 0.5, 0.5, 0.5, 0.1                     # disabled
CW_BUT_BGR_EN = 1, 1, 1, 0.2                            # enabled
CW_BUT_BGR_RES = 5, 5, 0, 1                             # sensor resetted


SENSOR_COLORS = {0: GREY,                           # disconnected
                 1: MO,                             # connected, standby
                 2: GREEN_BRIGHT,                   # connected, recording
                 3: GREEN_BRIGHT,                   # connected stimulating protocol on, but not stimulating
                 4: BLUE,                           # STIM on
                 }

# OTHER:
SPLASH_SCREEN_TIMEOUT = 2

# SETTINGS (change able in settings)
# TODO: replace other vars with these ones
SETTINGS_VAR = {"Main": {"app_version": "2.47.a4",
                         'title': "MooseWare",
                         'app_logo': '└┘┘┘┘=|◶◶|=└└└└┘',
                         }
                }

# KV FILE SPECIFIC:
STIM_PAR_HEIGHT = 0.9  # height of stimpar buttons
