#include "Adafruit_SGP30.h"

//Dummy Driver for Adafruit SGP30 driver

class SGP30 : public Adafruit_SGP30
{
    private:
    public:
        static const byte MAX_PARS = 16; // max pars for all sensors
        byte N_PARS = 3;                 // max pars for this sensor
        char NAME[32];                   // full name of sensor
        char SHORT_NAME[5];              // short name of sensor
        byte ADDRESS = 0x00;
        char PARAMETER_NAMES[MAX_PARS][16];      // name of parameters
        char PARAMETER_SHORT_NAMES[MAX_PARS][5]; // name of parameters
        uint error_count = 0;    
        unsigned long endtime;                // count errors
        int8_t STATUS = 0;
        bool startup = true;
        bool heatingUp;
        uint16_t sampled_data;

    SGP30() : Adafruit_SGP30()
    {
        strcpy(NAME, "SGP Sensor");
        strcpy(SHORT_NAME, "SGP");        
        ADDRESS = 0x58;
        N_PARS = 1;
        strcpy(PARAMETER_NAMES[0], "Parts per million, PPM");
        strcpy(PARAMETER_SHORT_NAMES[0], "PPM");
    }


    void init()
    {
        begin();
        if(startup)
        {
            heatingUp = true;
            endtime = millis() + 15000;
            startup = false;
        }
    }

    void sample()
    {
        if(heatingUp)
        {
            endtime = millis() + 15000;
            STATUS = 2; //heating up
        }
        if((heatingUp && endtime <= millis()))
        {
            heatingUp = false;
            STATUS = 0;
        }
        if(endtime <= millis())
        {
            IAQmeasure();
            sampled_data = TVOC;
            endtime= millis() + 1000;
        }
    }

    void dataToJSON(JsonObject js)
    {
        for (byte i=0; i < N_PARS; i++){
            js[PARAMETER_SHORT_NAMES[i]] = (float)(sampled_data);
            
        };
    }
};