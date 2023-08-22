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


class CarbonMonoxideSensor : public GasSensor
{
    private:
    public:
        //put in stuff here unit?


    CarbonMonoxideSensor(TwoWire &wire_in) : GasSensor(wire_in)
    {
        strcpy(NAME, "Carbon Monoxide Sensor");
        strcpy(SHORT_NAME, "CO");
        ADDRESS = 0x74; //this needed to be changed, currently overlaps with o2
        strcpy(PARAMETER_NAMES[1], "Parts per million, PPM");
        strcpy(PARAMETER_SHORT_NAMES[1], "PPM");
    }
   

    u_int16_t readGasConcPPM(uint8_t _temp)
    {
        u_int16_t Con;
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
           // Con *= 0.1; //Make sure to understand why at some point. Clear that for alt case its *= 0.01, not clear why all are a factor of 10 down...
        }
        if(tempComp == true)
        {
          if (((_temp) > -40) && ((_temp) <= 20))
          {
            Con = (Con / (0.005 * (_temp) + 0.9));
          }
          else if (((_temp) > 20) && ((_temp) < 40))
          {
            Con = (Con / (0.005 * (_temp) + 0.9) - (0.3 * (_temp)-6));
          }
          else
            Con = 0.0;
        }
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
        return Tbeta;
    }





};
