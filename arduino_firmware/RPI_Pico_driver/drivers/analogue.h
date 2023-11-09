/**
 * Driver for GPIO sampling and output
 *
 * USE GPIO number not pin number
 */

class Analogue : public Sensor
{
private:

public:
    Analogue() : Sensor()
    {
        strcpy(NAME, "Analogue");
        strcpy(SHORT_NAME, "ANLG");
        N_PARS = 2; // number of pins to sample
        strcpy(PARAMETER_NAMES[0], "CHANNEL 0");
        strcpy(PARAMETER_NAMES[1], "CHANNEL 1");
        strcpy(PARAMETER_SHORT_NAMES[0], "A0");
        strcpy(PARAMETER_SHORT_NAMES[1], "A1");

        // control_str = "["
        //               "{\"title\": \"GPIO Output\","
        //               "\"type\": \"stim\","
        //               "\"desc\": \"Create / Start / Stop gpio output protocol\","
        //               "\"live_widget\": true,"
        //               "\"key\": \"output\"}"
        //               "]";
    };
    void init()
    {
        analogReadResolution(12);  // set resolution to 12 bits
        // analogReadResolution(10);  // set resolution to 10 bits

        STATUS = 5;
    }

    void dataToJSON(JsonObject js)
    {
        js["A0"] = analogRead(A0);
        js["A1"] = analogRead(A1);
    };

    void procCmd(const char *key, JsonVariant value)
    {
        // incoming commandands are processed here
        // start stim
        // if (strcmp(key, "channel") == 0){
        //     channel_on_off(value.as<JsonArray>());
        //     }
    };
};