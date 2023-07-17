
 //for sgp30

class SGPSensor : public I2CSensor
{
    private:
    public:
        int16_t init = 0x2003;
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
        int8_t input[3];

    SGPSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "Generic Gas Resistance Sensor");
        strcpy(SHORT_NAME, "SGP Gas");        
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
        createInput(init);
        writeI2C(ADDRESS, init, &input, sizeof(input));
    }


    void sample()
    {
        if(heatingUp == true)
        {
             STATUS = 2; //heating up
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
            sampled_data = readGasConcPPM();//Commands to get data
            // status = 5; //Sampling? maybe 0? dont remember
        }


    }

    void reset_procedure() //Note: NOT chpip specific
    {
        //Note this is a general call reset, which, according to the manufacturer's documentation, will work on any chip that supports this generic protocol
        createInput(reset);
        writeI2C(ADDRESS, reset, &input, sizeof(input));
    }

    int16_t readGasConcPPM()
    {
        int8_t outputbuffer[6]; //input buffer
        createInput(measure);
        writeI2C(ADDRESS, measure, &input, sizeof(input));
        readI2C(ADDRESS, measure, 6, outputbuffer);
        return ((outputbuffer[2] << 8) + outputbuffer[3]);
    }


    void createInput(int16_t command)
    {
        &input = *command;
        input[2] = CalcCrc[command];
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


};