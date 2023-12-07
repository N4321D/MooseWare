// #include "i2csensor.h"  // (already included in arduino_send_interrupt.ino

class PSensor : public I2CSensor
{
private:
public:
    byte sampled_data[5]; // data is stored here

    // chip specific values:

    PSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        // strcpy(NAME, "Pressure Internal");
        // strcpy(SHORT_NAME, "PInt");
        // ADDRESS = 0x5C;
        N_PARS = 2;
        strcpy(PARAMETER_NAMES[0], "Pressure");
        strcpy(PARAMETER_NAMES[1], "Temperature");
        strcpy(PARAMETER_SHORT_NAMES[0], "PRS");
        strcpy(PARAMETER_SHORT_NAMES[1], "TMP");
    }

    void init()
    {
        // call to initialize sensor with correct settings
        STATUS = 5;
        byte out[1] = {0x50};
        writeI2C(ADDRESS, 0x10, 1, out); // set intial data ready & FIFO bits
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
        js["PRS"] = ((float)(((uint32_t)sampled_data[2] << 16) | ((uint32_t)sampled_data[1] << 8) | sampled_data[0])) / 5460.86912;
        js["TMP"] = ((float)(((uint32_t)sampled_data[4] << 8) | sampled_data[3])) / 100;
    }
};

class PInSensor : public PSensor
{
private:
public:
    PInSensor(TwoWire &wire_in) : PSensor(wire_in)
    {
        strcpy(NAME, "Pressure Internal");
        strcpy(SHORT_NAME, "PInt");
        ADDRESS = 0x5C;
    }
};

class PExSensor : public PSensor
{
private:
public:
    PExSensor(TwoWire &wire_in) : PSensor(wire_in)
    {
        strcpy(NAME, "Pressure External");
        strcpy(SHORT_NAME, "PExt");
        ADDRESS = 0x5D;
    }
};