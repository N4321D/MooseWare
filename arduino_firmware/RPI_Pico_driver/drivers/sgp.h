//{"CTRL": {"run": 1}}

class SGPSensor : public I2CSensor
{
    private:
    public:
        uint8_t MSB = 0x20; // Used for EVERY command other than reset.
        uint8_t initialize = 0x03;
        uint8_t measure = 0x08;
        uint8_t getBaseline = 0x15;
        uint8_t setBaseline = 0x1e;
        uint8_t setHumidity = 0x61;
        uint8_t rawMeasure = 0x50;
        int16_t reset = 0x0006;
        uint8_t reset1 = 06;
        uint8_t reset2 = 0x03;
        bool startup = true;
        bool heatingUp;
        bool tVOCmode;
        bool sampleReady;
        unsigned long endtime;
        unsigned long readDelay;
        uint16_t CO2buffer;
        uint8_t CRCs [2];
        uint16_t sampled_data;


    SGPSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "SGP Sensor");
        strcpy(SHORT_NAME, "SGP");        
        ADDRESS = 0x58;
        N_PARS = 1;
        strcpy(PARAMETER_NAMES[0], "Parts per billion, PPB");
        strcpy(PARAMETER_SHORT_NAMES[0], "PPB");        

    }


    void init()
    {
        Serial.println("checkpoint 1");
        if(startup){
            //boot up
            wire->beginTransmission(ADDRESS);
            wire->write(MSB);
            wire->write(initialize); //Boot up sequence
            wire->endTransmission();

            heatingUp = true;
            tVOCmode = true;
            sampleReady = false;
            endtime = millis() + 15000; //15 second heat up time
            startup = false;
            STATUS = 2;
        }
          //createInput(init);
        //writeI2C(ADDRESS, init, &input, sizeof(input));
    }


    void sample()
    {
        Serial.println("checkpoint 1.5");
        //if(!sgp.IAQmeasure()){Serial.println("Measure fail");}
        Serial.println("checkpoint 2");
        if(heatingUp && (endtime <= millis()))
        {
            heatingUp = false;
            STATUS = 0;
        }

        if(endtime <= millis() && tVOCmode) //Write Command tVOC
        {
            //sample: standard measurement of tVOC: calibrated based on H2 and Ethanol signals 
            wire->beginTransmission();
            wire->write(MSB);
            wire->write(measure);
            wire->endTransmission();
            //Delay of 12 ms needed
            readDelay = millis() + 12;
            endtime= millis() + 1000;
            sampleReady = true;
        }

        if(endtime <= millis() && !tVOCmode) //Write Command Raw
        {
            //sample: raw value readout. may require alternate calibration, TBD
            wire->beginTransmission();
            wire->write(MSB);
            wire->write(rawMeasure);
            wire->endTransmission();
            //Delay of 25 ms needed
            readDelay = millis() + 25;
            endtime= millis() + 1000;
            sampleReady = true;
        }        

        if(readDelay <= millis() && sampleReady) //Read data
        {
            wire->requestFrom(ADDRESS, 6);
            CO2buffer = wire->read() <<8;
            CO2buffer = wire->read();
            CRCs[0] = wire->read();
            sampled_data =wire->read() <<8;
            sampled_data =wire->read();
            sampleReady = false;
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

   /* int16_t readGasConcPPM()
    {
        int8_t outputbuffer[6]; //input buffer
        createInput(measure);
        //writeI2C(ADDRESS, measure, &input, sizeof(input));
        //readI2C(ADDRESS, measure, 6, outputbuffer);
        return ((outputbuffer[2] << 8) + outputbuffer[3]);
    }
*/

    /*void createInput(int16_t command)
    {
        uint8_t toPass[2]; //approach 2
        toPass[0] = (command >> 8) & (0xFF);//command MSB
        toPass[1] = command & 0xFF;//command LSB
        input = (uint8_t *)&command;  approach 1
        Serial.println(command);
        uint8_t data[2];
        *data = command;
        input[2] = CalcCrc(data);
        debug(data);
        junk[0] = toPass[0]; junk[1] = toPass[1]; junk[2] = CalcCrc(toPass);
        //Approach 3
        debug();
    }
    */

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
