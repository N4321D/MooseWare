#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/20231109/MooseWare/arduino_firmware/RPI_Pico_driver/drivers/carbondioxide.h"
/*
CO2 sensor using DFRobot SKU Sens 0159
UART only style sensor
*/
#include "uartsensor.h"
//Need to include this in the .ino file, rather than in this .h file

class CO2Sensor : public UARTSensor
{
    private:
    public:
        float sampled_data;


    CO2Sensor() : UARTSensor()
    {
        strcpy(NAME, "Carbon dioxide Resistance Sensor");
        strcpy(SHORT_NAME, "CO2");
        N_PARS = 1;
        strcpy(PARAMETER_NAMES[0], "Parts per million, PPM");
        strcpy(PARAMETER_SHORT_NAMES[0], "PPM");

    }


    void init()
    {
        setupSerial();
    }
    
    void reset_procedure()
    {
        //?????????
    }


    float readGasConcPPM(uint8_t _temp)
    {
        float Con = 0.0;
        uint8_t inputbuffer[6] = {0};
        uint8_t outputbuffer[9] = {0};
        inputbuffer[0] = GET_GAS_CONC;
        protocol _protocol = pack(inputbuffer, sizeof(inputbuffer));
        writeI2C(ADDRESS, 0, (uint8_t *)&_protocol, sizeof(_protocol));
        readI2C(ADDRESS, 0, 9, outputbuffer);
        if(FucCheckSum(outputbuffer, 8) == outputbuffer[8])
        {
            Con = ((outputbuffer[2]<<8) + outputbuffer[3]*1.0);
            Con *= 0.1; //Make sure to understand why at some point. Clear that for alt case its *= 0.01, not clear why all are a factor of 10 down...
        }
        return Con;
    }

    void dataToJSON(JsonObject js)
    {
        for (byte i=0; i < N_PARS; i++){
            js[PARAMETER_SHORT_NAMES[i]] = ((float)sampled_data[i]);
            
        };
    }

};