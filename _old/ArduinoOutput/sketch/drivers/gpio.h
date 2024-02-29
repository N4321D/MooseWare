#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/20231109/MooseWare/arduino_firmware/RPI_Pico_driver/drivers/gpio.h"
/**
 * Driver for GPIO sampling and output
 *
 * USE GPIO number not pin number
 */

class GPIObus : public Sensor
{
private:
    bool stim_amp = 0;
    unsigned long stim_end = 0;

public:
    GPIObus() : Sensor()
    {
        strcpy(NAME, "GPIO Interface");
        strcpy(SHORT_NAME, "GPIO");
        N_PARS = 2; // number of pins to sample
        strcpy(PARAMETER_NAMES[0], "GPIO 6 IN");
        strcpy(PARAMETER_NAMES[1], "GPIO 7 OUT");
        strcpy(PARAMETER_SHORT_NAMES[0], "IN");
        strcpy(PARAMETER_SHORT_NAMES[1], "OUT");

        control_str = "["
                      "{\"title\": \"GPIO Output\","
                      "\"type\": \"stim\","
                      "\"desc\": \"Create / Start / Stop gpio output protocol\","
                      "\"live_widget\": true,"
                      "\"key\": \"output\"}"
                      "]";
    };
    void init()
    {
        STATUS = 5;
        pinMode(6, INPUT_PULLDOWN);
        pinMode(7, OUTPUT);
    }

    void sample()
    {
        check_stim();
    }

    void dataToJSON(JsonObject js)
    {
        js["IN"] = digitalRead(6);
        js["OUT"] = digitalRead(7);
    };

    void check_stim()
    {
        if (stim_amp)
        {
            if (millis() >= stim_end)
            {
                // stop stim
                stim_amp = 0;
                setGpio(stim_amp);
            }
        }
    };

    void setGpio(bool state)
    {
        STATUS = state ? 10 : 5;
        digitalWrite(7, state);
    };

    void start_stim(JsonArray time_amps)
    {
        stim_end = millis() + time_amps[0].as<unsigned long>();
        stim_amp = time_amps[1].as<bool>();
        setGpio(stim_amp);
    }

    void procCmd(const char *key, JsonVariant value)
    {
        // incoming commandands are processed here
        // start stim
        if (strcmp(key, "output") == 0){
            start_stim(value.as<JsonArray>());
            }
    };
};