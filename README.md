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

## Description 
Recording software to record from Neureflect inc. patented devices. This repository consists of micro controller drivers for RPI Pico written in C++ (Arduino IDE) and the control / GUI software which can run on multiple devices written in python.

## Installation
### GUI / Recording Software:
Install python rec_app with poetry for easy installation:
1. install poetry (see: https://python-poetry.org/)
2. clone repository
3. goto folder where repository is and run `poetry install`
4. to start: make sure the poetry env is activated `poetry shell`, then goto the rec_app folder and run the main.py file

### Micro controller driver:
Copy / install arduino_firmware folder to RPI pico using arduino ide
