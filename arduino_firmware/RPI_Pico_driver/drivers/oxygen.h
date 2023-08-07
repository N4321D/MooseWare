/**
 * Template for generic gas driver. Must be imported for drivers of the specific sensors from DFRobot for ammonia, carbon monoxide, etc.
 * 
 * 
 * 
 * 
 * 
 * 
 * */
//#include <gas.h>
//#include <i2csensor.h>>


class OxygenSensor : public GasSensor
{
    private:
    public:
        //put in stuff here unit?


    OxygenSensor(TwoWire &wire_in) : GasSensor(wire_in)
    {
        strcpy(NAME, "Oxygen Resistance Sensor");
        strcpy(SHORT_NAME, "O2");
        ADDRESS = 0x75; //need to readd o2 sensor to pico driver
        strcpy(PARAMETER_NAMES[1], "Percent by Volume");
        strcpy(PARAMETER_SHORT_NAMES[1], "% Vol");
    }
 
  
    uint16_t readGasConcPPM(uint8_t _temp)
    {
        uint16_t Con;
        uint8_t inputbuffer[6] = {0};
        uint8_t outputbuffer[9] = {0};
        inputbuffer[0] = GET_GAS_CONC;
        protocol _protocol = pack(inputbuffer, sizeof(inputbuffer));
        writeI2C(ADDRESS, 0, (uint8_t *)&_protocol, sizeof(_protocol));
        readI2C(ADDRESS, 0, 9, outputbuffer);
        //readOutput(outputbuffer);
        if(FucCheckSum(outputbuffer, 8) == outputbuffer[8])
        {
            Con = (uint16_t)((outputbuffer[2]<<8) | outputbuffer[3]);
            Con *= 0.1; //do this right later (bit shifting)
        }
       // Serial.println(Con);
        return Con;
    }

    uint16_t readTempC()
    {
        uint8_t inputbuffer[6] = {0};
        uint8_t outputbuffer[9] = {0};
        inputbuffer[0] = GET_TEMP;
        protocol _protocol = pack(inputbuffer, sizeof(inputbuffer));
        writeI2C(ADDRESS, 0, (uint8_t *)&_protocol, sizeof(_protocol));
        readI2C(ADDRESS, 0, 9, outputbuffer); 
        if(FucCheckSum(outputbuffer, 8) != outputbuffer[8])
        {
            return 0;
        }       

        uint16_t temp_ADC = (uint16_t)((outputbuffer[2]<<8) | outputbuffer[3]);
       //register is 0x87; need to get ADC value from chip
       // uint16_t temp_ADC = (recvbuf[2] << 8) + recvbuf[3];
        float Vpd3=3*(float)temp_ADC/1024;
        float Rth = Vpd3*10000/(3-Vpd3);
        float Tbeta = 1/(1/(273.15+25)+1/3380.13*log(Rth/10000))-273.15;
        //Serial.println(Tbeta);
        return Tbeta;
    }





};
