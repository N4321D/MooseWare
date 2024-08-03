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
Recording software to record from Neureflect inc. patented devices. This repository consists of the control / GUI software which can run on multiple devices written in python and the drivers for the internal I2C and GPIO ports of the Rapberry Pi.

## Installation
### GUI / Recording Software:
Install python rec_app with poetry for easy installation:
1. install poetry (see: https://python-poetry.org/)
2. clone repository
3. go to the folder where the repository is and run `poetry install`

## Hardware
Tested and running on most Linux devices including Rapsbian Bookworm Lite on the Raspberry Pi 4. Should also run on Windows and OSX devices, but testing has been limited. Connects to microcontroller over USB serial to record.

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
This project is licensed under the MIT License for non-commercial use. For commercial use, please contact me.

### Non-Commercial Use
You are free to use, modify, and distribute this software for non-commercial purposes under the terms of the MIT License.

### Commercial Use
For commercial use, please reach out to me at dmitri@neureflect.com
