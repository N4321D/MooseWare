#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/20231109/MooseWare/arduino_firmware/RPI_Pico_driver/drivers/motion.h"
/**
 * Driver for movement sensor LMS6DS3
 *
 * */

class MOTSensor : public I2CSensor
{
private:
public:
    // chip specific values:
    int16_t sampled_data[6]; // data is stored here

    static constexpr byte ang_sens_bytes[5] = {0b10000010, 0b10000000, 0b10000100, 0b10001000, 0b10001100};
    float ang_sens_vals[5] = {2.18, 4.36, 8.73, 17.45, 34.91};
    const char ang_sens_unit[6] = "rad/s";
    static constexpr byte lin_sens_bytes[4] = {0b10010000, 0b10011000, 0b10011100, 0b10010100};
    byte lin_sens_vals[4] = {2, 4, 8, 16};
    const char lin_sens_unit[2] = "g";
    byte ang_sensitivity = 2;
    byte lin_sensitivity = 0;

    MOTSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "Motion Sensor");
        strcpy(SHORT_NAME, "MOT");
        ADDRESS = 0x6B;
        N_PARS = 6;
        strcpy(PARAMETER_NAMES[0], "Motion Ang. X");
        strcpy(PARAMETER_NAMES[1], "Motion Ang. Y");
        strcpy(PARAMETER_NAMES[2], "Motion Ang. Z");
        strcpy(PARAMETER_NAMES[3], "Motion Lin. X");
        strcpy(PARAMETER_NAMES[4], "Motion Lin. Y");
        strcpy(PARAMETER_NAMES[5], "Motion Lin. Z");
        strcpy(PARAMETER_SHORT_NAMES[0], "AX");
        strcpy(PARAMETER_SHORT_NAMES[1], "AY");
        strcpy(PARAMETER_SHORT_NAMES[2], "AZ");
        strcpy(PARAMETER_SHORT_NAMES[3], "LX");
        strcpy(PARAMETER_SHORT_NAMES[4], "LY");
        strcpy(PARAMETER_SHORT_NAMES[5], "LZ");
        control_str = "["
                      "{\"title\": \"Angular Sensitivity\","
                      "\"type\": \"options\","
                      "\"desc\": \"Sensitivity of the angular movement sensor in rad/s.\","
                      "\"key\": \"asens\","
                      "\"default_value\": 8.73,"
                      "\"options\": [2.18, 4.36, 8.73, 17.45, 34.91]},"
                      "{\"title\": \"Linear Sensitivity\","
                      "\"type\": \"options\","
                      "\"desc\": \"Sensitivity of the linear movement sensor in g\","
                      "\"key\": \"lsens\","
                      "\"default_value\": 2,"
                      "\"options\": [2, 4, 8, 16]}"
                      "]";
    }

    void init()
    {
        // call to initialize sensor with correct settings
        const byte reglist[14] = {0x01, 0x04, 0x06, 0x07, 0x08, 0x09,
                                  0x0A, 0x0B, 0x13, 0x14, 0x15, 0x16,
                                  0x17, 0x1A};

        for (byte i = 0; i < 14; i++)
        {
            writeI2C(ADDRESS, reglist[i], 1, 0x00);
        };

        byte data = 0b01000000;
        writeI2C(ADDRESS, 0x0D, 1, &data); // set intial data ready & FIFO bits
        data = 0b00000011;
        writeI2C(ADDRESS, 0x0E, 1, &data); // set initial data ready bits
        data = 0b00000100;
        writeI2C(ADDRESS, 0x12, 1,  &data); // set to i2c mode
        data = 0b00111000;
        writeI2C(ADDRESS, 0x18, 1, &data); // enable X Y and Z axis on linear sensor
        writeI2C(ADDRESS, 0x19, 1, &data); // enable X Y and Z axis on angular sensor

        set_lin_sensitivity();
        set_ang_sensitivity();
        STATUS = 5;
    }

    void sample()
    {
        if (readI2C(ADDRESS, 0x22, 12, &sampled_data))
        {
            error_count = 0;
        }
        else
        {
            error_count++;
        };
    };

    // chip specific functions
    void set_ang_sensitivity(float sensitivity = 0.0)
    {
        if (sensitivity != 0.0)
        {
            // find position of value in index
            for (byte i = 0; i < 6; i++)
            {
                if (sensitivity == ang_sens_vals[i])
                {
                    ang_sensitivity = i;
                    break;
                };
            };
        };
        writeI2C(ADDRESS, 0x11, 1, &ang_sens_bytes[ang_sensitivity]);
    }

    void set_lin_sensitivity(byte sensitivity = 0xff)
    {
        if (sensitivity != 0xff){
            // find position of value in index
            for (byte i = 0; i < 5; i++)
            {
                if (sensitivity == lin_sens_vals[i])
                {
                    lin_sensitivity = i;
                    break;
                };
            };
        };
        writeI2C(ADDRESS, 0x10, 1, &lin_sens_bytes[lin_sensitivity]);
    }

    void reset_procedure()
    {
        byte data = 0x01;
        writeI2C(ADDRESS, 0x12, 1,  &data);
    }

    // chip specific functions
    void dataToJSON(JsonObject js)
    {
        for (byte i = 0; i < N_PARS; i++)
        {
            if (i < 3)
                js[PARAMETER_SHORT_NAMES[i]] = ((float)sampled_data[i] / 0x7FFF) * ang_sens_vals[ang_sensitivity];
            else
                js[PARAMETER_SHORT_NAMES[i]] = ((float)sampled_data[i] / 0x7FFF) * lin_sens_vals[lin_sensitivity] * 2; // *2 is because range is +/-
        };
    }

    void procCmd(const char *key, JsonVariant value)
    {
        // incoming commandands are processed here

        // set sensitivity
        if (strcmp(key, "asens") == 0)
            set_ang_sensitivity(value.as<float>());
        if (strcmp(key, "lsens") == 0)
            set_lin_sensitivity(value.as<unsigned short>());
    }
};