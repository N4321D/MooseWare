#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/drivers/ois.h"
// #include "i2csensor.h"  // (already included in arduino_send_interrupt.ino

class OISSensor : public I2CSensor
{
private:
    unsigned long stim_end;
    byte stim_amp = 0;

public:
    uint16_t sampled_data[2]; // data is stored here

    // chip specific values:
    byte green_amps = 5; // green led mA
    static const byte MAX_AMP = 63;

    OISSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "Optical Intrisic Signal");
        strcpy(SHORT_NAME, "OIS");
        ADDRESS = 0x5B;
        N_PARS = 3;
        strcpy(PARAMETER_NAMES[1], "OIS Signal");
        strcpy(PARAMETER_NAMES[0], "OIS Background");
        strcpy(PARAMETER_NAMES[2], "OIS Stimulation mA");
        strcpy(PARAMETER_SHORT_NAMES[1], "SIG");
        strcpy(PARAMETER_SHORT_NAMES[0], "BGR");
        strcpy(PARAMETER_SHORT_NAMES[2], "STIM");

        control_str = "[{\"title\": \"Green Led Intensity\","
            "\"type\": \"plusminin\","
            "\"desc\": \"Power in mA of the green LEDs\","
            "\"section\": \"recording\","
            "\"key\": \"ois_ma\","
            "\"steps\": [[0, 10, 1], [10, 20, 2], [20, 100, 10]]," // [min of range, max of range, step in range]
            "\"limits\": [0, 65],"                                 // [min, max]
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
         *   0: "green"
         *   1: "ir / blue"
         */

        const byte out = green ? 0x87 : 0x97;
        writeI2C(ADDRESS, 0x41, &out, 1);
    }

    void set_amps(byte amp, bool ir = false)
    {
        if (amp > MAX_AMP)
            amp = MAX_AMP;

        static byte out[2];

        if (!ir)
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
                set_amps(green_amps, false);
                set_mode(true);
            }
        }
    }

    void start_stim(JsonArray time_amps)
    {
        stim_end = millis() + time_amps[0].as<unsigned long>();
        byte amp = time_amps[1].as<unsigned short>();
        if (amp > 0)
        {
            set_amps(amp, true);
            set_mode(false);
        }
        else
        {
            set_amps(green_amps, false);
            set_mode(true);
        }
    }

    // chip specific functions
    void dataToJSON(JsonObject js)
    {
        js["SIG"] = (float)sampled_data[1] / 0xFFFF;
        js["BGR"] = (float)sampled_data[0] / 0xFFFF;
        js["STIM"] = stim_amp;
    }

    void procCmd(const char *key, JsonVariant value)
    {
        // incoming commandands are processed here

        // set led amps
        if (strcmp(key, "amps") == 0)
            set_amps(value.as<unsigned short>());
        if (strcmp(key, "stim") == 0)
            start_stim(value.as<JsonArray>());
    }

    void stop()
    {
        // stop stim
        set_amps(green_amps, false);
        set_mode(true);
    }
};
