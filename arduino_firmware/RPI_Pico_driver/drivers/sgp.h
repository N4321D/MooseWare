
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
        int16_t sampled_data;
        uint8_t junk[3];

    SGPSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "Generic Gas Resistance 3Sensor");
        strcpy(SHORT_NAME, "SGP");        
        ADDRESS = 0x58;
        N_PARS = 1;
        strcpy(PARAMETER_NAMES[0], "Parts per million, PPM");
        strcpy(PARAMETER_SHORT_NAMES[0], "PPM");        


    }
    
    void init()
    {
        if(startup){
            heatingUp = true;
            endtime = millis() + 15000; //15 second heat up time
            startup = false;
        }
        createInput(initial);
        writeI2C(ADDRESS, initial, junk, sizeof(junk));

    }

    void sample()
    {
        if(heatingUp == true)
        {
             STATUS = 2; //heating up
             //Serial.println("Boot up successful");
             sampled_data = readGasConcPPM();

            if(endtime <= millis())
            {
                heatingUp = false;
                STATUS = 0; //done heating up
            }
            //status = 2;
        }
        else
        {
            if(endtime <= millis())
            {
                sampled_data = readGasConcPPM();//Commands to get data
                endtime = millis() + 1000;
            }
            // status = 5; //Sampling? maybe 0? dont remember
        }

    }

    void reset_procedure() //Note: NOT chpip specific
    {
        //Note this is a general call reset, which, according to the manufacturer's documentation, will work on any chip that supports this generic protocol
        createInput(reset);
        writeI2C(ADDRESS, reset, junk, sizeof(junk));
    }

    int16_t readGasConcPPM()
    {
        int8_t outputbuffer[6]; //input buffer
        createInput(measure);
        if(writeI2C(ADDRESS, measure, junk, sizeof(junk)))
        {
            Serial.println("Successful write of record command");
        }
        else{
            Serial.println("record fail");
        }
        readI2C(ADDRESS, measure, 6, outputbuffer);
        Serial.println(outputbuffer[2]);
        Serial.println(outputbuffer[3]);
        return ((outputbuffer[2] << 8) + outputbuffer[3]*1.0);
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
            for(uint8_t bit = 8; bit > 0; --bit)
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

    void dataToJSON(JsonObject js)
    {
        for (byte i=0; i < N_PARS; i++){
            js[PARAMETER_SHORT_NAMES[i]] = ((float)sampled_data);
            
        };
    }


    void debug()
    {
        for(int y = 0; y < sizeof(junk); y++)
        {
            Serial.println(junk[y],HEX);
        }
    }
};