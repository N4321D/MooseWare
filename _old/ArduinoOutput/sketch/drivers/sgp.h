#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/20231109/MooseWare/arduino_firmware/RPI_Pico_driver/drivers/sgp.h"
//{"CTRL": {"run": 1}}
//{"CTRL": {"freq": .5}}

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
        //wire = &wire_in;
        strcpy(NAME, "SGP Sensor");
        strcpy(SHORT_NAME, "SGP");        
        ADDRESS = 0x58;
        N_PARS = 1;
        strcpy(PARAMETER_NAMES[0], "Parts per billion, PPB");
        strcpy(PARAMETER_SHORT_NAMES[0], "PPB");        

    }


    void init()
    {
        if(startup){
            //boot up
            delay(1000);
            Wire1.beginTransmission(ADDRESS);
            Wire1.write(0x20);
            Wire1.write(0x03); //Boot up sequence
            Wire1.endTransmission();
            delay(1000);
            heatingUp = true;
            tVOCmode = true;
            sampleReady = false;
            endtime = millis() + 15000; //15 second heat up time
            startup = false;
            STATUS = 2;
        }
          //createInput(init);
    }


    void sample()
    {
       // init();
       if(!startup)
       {
            if(endtime <= millis()){STATUS = 0;}
            Wire1.beginTransmission(ADDRESS);  // open com
            Wire1.write(0x20);                      // command start measurement (raw measurement is x2050), NO CRC needed
            Wire1.write(0x08);
            Wire1.endTransmission();   // close transmission, has to be done so that chip starts the measurement
            delay(20);
            CO2buffer = Wire1.read()<<8;
            CO2buffer += Wire1.read();
            CRCs[0] = Wire1.read();
            sampled_data = Wire1.read()<<8;
            sampled_data += Wire1.read();
            CRCs[1] = Wire1.read();
      
            
            delay(1000);

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
