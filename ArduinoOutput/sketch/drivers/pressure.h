#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/drivers/pressure.h"
// #include "i2csensor.h"  // (already included in arduino_send_interrupt.ino

class PInSensor : public I2CSensor
{
private:
public:
    byte sampled_data[5]; // data is stored here

    // chip specific values:

    PInSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "Pressure Internal");
        strcpy(SHORT_NAME, "PInt");
        ADDRESS = 0x5C;
        N_PARS = 2;
        strcpy(PARAMETER_NAMES[0], "Pressure");
        strcpy(PARAMETER_NAMES[1], "Temperature");
        strcpy(PARAMETER_SHORT_NAMES[0], "PR");
        strcpy(PARAMETER_SHORT_NAMES[1], "TMP");


    }

    void init()
    {
        // call to initialize sensor with correct settings
        STATUS = 5;
        byte out[1] = {0x50};
        writeI2C(ADDRESS, 0x10, out, 1); // set intial data ready & FIFO bits
    }

    void sample()
    {
        if (readI2C(ADDRESS, 0x28, 5, &sampled_data))
        {
            error_count = 0;
        }
        else
        {
            error_count++;
        };
    };

    // chip specific functions
    void dataToJSON(JsonObject js)
    {
        js["PR1"] = ((float)(((uint32_t)sampled_data[2] << 16) | ((uint32_t)sampled_data[1] << 8) | sampled_data[1])) / 5460.86912;
        js["TMP"] = ((float)(((uint32_t)sampled_data[4] << 8) | sampled_data[3])) / 100;
    }
};