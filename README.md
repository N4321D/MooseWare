# MooseWare

```
     ___            ___ 
    /   \          /   \
   \_   \        /  __/
     _\   \      /  /__ 
     \___  \____/   __/ 
         \_       _/    
           | @ @  \_    
           |            
         _/     /\      
        /o)  (o/\ \_    
        \_____/ /       
          \____/        
                                                    NEUREFLECT INC.
|   |   | /   \  /   \ /    /  /   ]  |  |  | /    ||    \   /   ]
|       ||     ||     (   \   /  [ |  |  |  ||  o  ||  D  ) /  [  
|  \ /  ||  O  ||  O  |\    ||     ]  |  |  ||     ||    / |     ]
|   |   ||     ||     |/  \ ||   [ |  '  '  ||     ||    \ |   [  
|   |   ||     ||     |\    ||     |\      / |  |  ||  .  \|     |
|   |   | \   /  \   /  \   ||     | \ /\ /  |  |  ||  |\ ||     |
```

**Neureflect**<sup>inc</sup> 2023  
Recording Software  
*by Dmitri Yousef Yengej*


## Table of Contents

- [Description](#description)
- [Installation](#Installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Description 
Recording software to record from Neureflect inc. patented devices. This repository consists of micro controller drivers for RPI Pico written in C++ (Arduino IDE) and the control / GUI software which can run on multiple devices written in python.

## Installation
### GUI / Recording Software:
Install python rec_app with poetry for easy installation:
1. install poetry (see: https://python-poetry.org/)
2. clone repository
3. goto folder where repository is and run `poetry install`

### Micro controller driver:
To use this Arduino sketch, follow these steps:

1. Install the Arduino IDE and the RPI pico board plugins if you haven't already.
2. Open the Arduino IDE and create a new sketch.
3. Load the contents of the provided `arduino_send_interrupt` folder into your new sketch.
4. Install the latest versions of these libraries: "Adafruit_SSD1306", "Adafruit_GFX", "RPi_Pico_TimerInterrupt"  and "ArduinoJson" 
5. Connect your RPi pico board to your computer.
6. Select the appropriate board and port from the "Tools" menu.
7. Upload the sketch to your board.

## Usage
To start make sure the poetry env is activated `poetry shell`, then go to the rec_app folder and run the main.py file

## Contributing
Contributions to this code are welcome! If you find bugs or want to add features, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and test them thoroughly.
4. Commit your changes and push to your forked repository.
5. Open a pull request to the main repository.

## License

