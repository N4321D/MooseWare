 #include "Adafruit_SGP30.h"
 //for sgp30
//{"CTRL": {"run": 1}}

class SGPSensor : public I2CSensor
{
    private:
    public:
        int16_t initial = 0x2003;
        int16_t measure = 0x2008;
        int16_t getBaseline = 0x2015;
        int16_t setBaseline = 0x201e;
        int16_t setHumidity = 0x2061;
        int16_t rawMeasure = 0x2050;
        int16_t reset = 0x0006;
        bool startup = true;
        bool heatingUp;
        unsigned long endtime;
        uint16_t sampled_data;
        int8_t junk[3];
        Adafruit_SGP30 sgp;


    SGPSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        sgp = Adafruit_SGP30();
        strcpy(NAME, "SGP Sensor");
        strcpy(SHORT_NAME, "SGP");        
        ADDRESS = 0x58;
        N_PARS = 1;
        strcpy(PARAMETER_NAMES[0], "Parts per million, PPM");
        strcpy(PARAMETER_SHORT_NAMES[0], "PPM");        


    }


    void init()
    {
        Serial.println("checkpoint 1");
        if(startup){
            heatingUp = true;
            endtime = millis() + 15000; //15 second heat up time
            startup = false;
        }
        if(!sgp.begin()){Serial.println("Initialize fail");}
        //createInput(init);
        //writeI2C(ADDRESS, init, &input, sizeof(input));
    }


    void sample()
    {
        if(startup){init();}
        Serial.println("checkpoint 1.5");
        //if(!sgp.IAQmeasure()){Serial.println("Measure fail");}
        Serial.println("checkpoint 2");
        if(heatingUp)
        {
            endtime = millis() + 15000;
            STATUS = 2; //heating up
        }
        if(heatingUp && (endtime <= millis()))
        {
            heatingUp = false;
            STATUS = 0;
        }
        if(endtime <= millis())
        {
            if(!sgp.IAQmeasure()){Serial.println("Measure fail");}
            sampled_data = sgp.TVOC;
            endtime= millis() + 1000;
        }

    }

    void dataToJSON(JsonObject js)
    {
        for (byte i=0; i < N_PARS; i++){
            js[PARAMETER_SHORT_NAMES[i]] = ((float)sampled_data);
            
        };
    }

    void reset_procedure() //Note: NOT chpip specific
    {
        //Note this is a general call reset, which, according to the manufacturer's documentation, will work on any chip that supports this generic protocol
        //createInput(reset);
        //writeI2C(ADDRESS, reset, &input, sizeof(input));
    }

    int16_t readGasConcPPM()
    {
        int8_t outputbuffer[6]; //input buffer
        createInput(measure);
        //writeI2C(ADDRESS, measure, &input, sizeof(input));
        //readI2C(ADDRESS, measure, 6, outputbuffer);
        return ((outputbuffer[2] << 8) + outputbuffer[3]);
    }


    void createInput(int16_t command)
    {
        uint8_t toPass[2]; //approach 2
        toPass[0] = (command >> 8) & (0xFF);//command MSB
        toPass[1] = command & 0xFF;//command LSB
       /* *input = (uint8_t *)&command;  approach 1
        Serial.println(command);
        uint8_t data[2];
        *data = command;
        input[2] = CalcCrc(data);
        debug(data);*/
        junk[0] = toPass[0]; junk[1] = toPass[1]; junk[2] = CalcCrc(toPass);
        //Approach 3
        debug();
    }

    uint8_t CalcCrc(uint8_t data[2])
    {
        uint8_t crc = 0xFF;
        for(int i =0; i < 2; i++)
        {
            crc ^= data[i];
            for(uint8_t bit = 8; bit > 0; bit--)
            {
                if(crc & 0x80)
                {
                    crc = (crc << 1) ^ 0x31u;
                }
                else
                {
                    crc = (crc <<1);
                }
            }
        }
        return crc;
    }


    void debug()
    {
        for(int y = 0; y < sizeof(junk); y++)
        {
            Serial.println(junk[y],HEX);
        }
    }

};
