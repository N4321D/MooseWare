// #include "i2csensor.h"  // (already included in arduino_send_interrupt.ino

class OISSensor : public I2CSensor
{
private:
    // chip specific values:
    byte green_amps = 5; // green led mA
    static const byte MAX_AMP = 63;
    unsigned long stim_end;
    byte stim_amp = 0;

public:
    uint16_t sampled_data[2]; // data is stored here

    OISSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "Optical Intrisic Signal");
        strcpy(SHORT_NAME, "OIS");
        ADDRESS = 0x5B;
        N_PARS = 4;
        strcpy(PARAMETER_NAMES[1], "OIS Signal");
        strcpy(PARAMETER_NAMES[0], "OIS Background");
        strcpy(PARAMETER_NAMES[2], "OIS Stimulation mA");
        strcpy(PARAMETER_NAMES[3], "OIS Green LED mA");
        strcpy(PARAMETER_SHORT_NAMES[1], "SIG");
        strcpy(PARAMETER_SHORT_NAMES[0], "BGR");
        strcpy(PARAMETER_SHORT_NAMES[2], "STIM");
        strcpy(PARAMETER_SHORT_NAMES[3], "PWR");

        control_str = "["
                      "{\"title\": \"Blue Light Stimulation\","
                      "\"type\": \"stim\","
                      "\"desc\": \"Create / Start / Stop blue light stimulation protocol\","
                      "\"key\": \"stim\"},"
                      "{\"title\": \"Green Led Intensity\","
                      "\"type\": \"plusminin\","
                      "\"desc\": \"Green LED power in %\","
                      "\"key\": \"amps\","
                      "\"steps\": [[0, 10, 1], [10, 20, 2], [20, 60, 5], [60, 200, 10]]," // [min of range, max of range, step in range]
                      "\"limits\": [0, 100],"                                             // [min, max]
                      "\"default_value\": 25,"
                      "\"live_widget\": true}"
                      "]";
    }
    void init()
    {
        // call to initialize sensor with correct settings
        set_mode(true);
        set_amps(green_amps);
    }

    void trigger()
    {
        // trigger reading if nescessary
        static byte out[1] = {0x01};
        writeI2C(ADDRESS, 0x47, out, 1); // trigger one shot reading
    }

    void sample()
    {
        check_stim();
        if (readI2C(ADDRESS, 0x54, 4, &sampled_data))
        {
            error_count = 0;
        }
        else
        {
            error_count++;
        };
    };

    // chip specific functions

    void set_mode(bool green = true)
    {
        /*
         * modes:
         *   0: "ir"
         *   1: "green"
         */
        STATUS = green ? 5 : 10;
        const byte out = green ? 0x87 : 0x97;
        writeI2C(ADDRESS, 0x41, &out, 1);
    }

    void set_amps(byte amp, bool green = true)
    {
        if (amp > MAX_AMP)
            amp = MAX_AMP;

        static byte out[2];

        if (green)
        {
            green_amps = amp;
            out[0] = amp;
            out[1] = amp;
        }
        else
        {
            stim_amp = amp;
            out[0] = static_cast<byte>(0b10 << 6 | amp);
            out[1] = static_cast<byte>(0b1 << 7 | amp);
        }
        writeI2C(ADDRESS, 0x42, out, 2);
    }

    void check_stim()
    {
        if (stim_amp > 0)
        {
            if (millis() >= stim_end)
            {
                // stop stim
                stim_amp = 0;
                set_amps(green_amps, true);
                set_mode(true);
            }
        }
    }

    void start_stim(JsonArray time_amps)
    {
        stim_end = millis() + time_amps[0].as<unsigned long>();
        byte amp = (byte)((time_amps[1].as<float>() / 100) * MAX_AMP);
        if (amp > 0)
        {
            // pulse on
            set_amps(amp, false);
            set_mode(false);
        }
        else
        {
            // pulse off
            set_amps(green_amps, true);
        }
    }

    // chip specific functions
    void dataToJSON(JsonObject js)
    {
        js["SIG"] = (float)sampled_data[1] / 0xFFFF;
        js["BGR"] = (float)sampled_data[0] / 0xFFFF;
        js["STIM"] = stim_amp;
        js["PWR"] = green_amps;
    }

    void procCmd(const char *key, JsonVariant value)
    {
        // incoming commandands are processed here

        // set led amps
        if (strcmp(key, "amps") == 0)
            set_amps((byte)((value.as<float>() / 100) * MAX_AMP), true);
        // start stim
        if (strcmp(key, "stim") == 0)
            start_stim(value.as<JsonArray>());
    }

    void stop()
    {
        // stop stim
        set_amps(green_amps, true);
        set_mode(true);
    }
};
