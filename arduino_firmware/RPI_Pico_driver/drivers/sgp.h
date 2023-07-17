
 //for sgp30

class SGPSensor : public I2CSensor
{
    private:
    public:



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
        
    }


    void sample()
    {



    }

    void reset_procedure()
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

    }

};