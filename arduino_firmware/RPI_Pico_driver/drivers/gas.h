/**
 * Template for generic gas driver. Must be imported for drivers of the specific sensors from DFRobot for ammonia, carbon monoxide, etc.
 * 
 * 
 * 
 * Generic driver for the DFRobot 
 * 
 * 
 * */
//#include <i2csensor.h>
//#include math //?

class GasSensor : public I2CSensor
{
    private:
    public:
        //put in stuff here
        byte CHANGE_I2C_ADDR = 0x92;
        byte GET_GAS_CONC = 0x86;
        byte GET_TEMP = 0x87;
        byte GET_VOLTAGE = 0x91;
        byte CHANGE_MODE = 0X78;
        bool mode;
        bool tempComp = false;

    GasSensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        strcpy(NAME, "Gas Resistance Sensor");
        strcpy(SHORT_NAME, "GAS");
        N_PARS = 2;
        uint8_t ADDRESS;
        strcpy(PARAMETER_NAMES[0], "Temperature, deg C");
        strcpy(PARAMETER_NAMES[1], "Parts per million, PPM");
        strcpy(PARAMETER_SHORT_NAMES[0], "Temp");
        strcpy(PARAMETER_SHORT_NAMES[1], "PPM");



    }


    typedef struct //Thing to pass to Sensor
    {
        uint8_t head;
        uint8_t addr;
        uint8_t data[6];
        uint8_t check;
    } protocol;


    protocol pack(uint8_t *pBuffer, uint8_t len) //Compresses modified aspects of the array to the protocol struct
    {
        protocol _protocol;
        _protocol.head = 0xff;
        _protocol.addr = 0x01;
        memcpy(_protocol.data, pBuffer, len);
        _protocol.check = FucCheckSum((uint8_t*)&_protocol, 8);
        return _protocol;
    }


    unsigned char FucCheckSum(unsigned char *i,unsigned char ln)
    {
        unsigned char j,tempq=0;
        i+=1;
        for(j=0;j<(ln-2);j++)
        {
            tempq+=*i;
            i++;
        }


        tempq=(~tempq)+1;
        return(tempq);
    }


    void init()
    {
        changeAcquireMode(true);
        //Sets chip to active sampling
        delay(1000); //Documentation recommends allowing 5 minutes for sensor to get going. If "long time" before last use, recommends up to 24 hrs
    }


    void sample()
    {
       sampled_data[0] = readTempC();
       Serial.println(String(sampled_data[0]));
       sampled_data[1] = readGasConcPPM(sampled_data[0]);
       Serial.println(String(sampled_data[1]));
       for(byte i=0; i < N_PARS; i++)
       {
        if(sampled_data[i] == 0.0) {error_count++;}
       }

    }    

    bool changeAcquireMode(bool active)
    {
        mode = active;
        byte tosend;
        if (active == true) {tosend = 0x03;}//active data collection
        else {tosend == 0x04;}//must be sampled manually (sleep??)
        uint8_t inputbuffer[6] = {0};
        uint8_t outputbuffer[9] = {0};
        inputbuffer[0] = CHANGE_MODE;
        inputbuffer[1] = tosend;
        protocol _protocol = pack(inputbuffer, sizeof(inputbuffer));
        if(!writeI2C(ADDRESS, 0, (uint8_t *)&_protocol, sizeof(_protocol))){Serial.println("Write failure");}
        if(!readI2C(ADDRESS, 0, 9, outputbuffer)){Serial.println("Read failure");}
        if (outputbuffer[2] == 1){return true;}
        else 
        {
            Serial.println("Mode change failure");
            return false;
        } //validates whether the mode change was successful   
    }

     void reset_procedure()
    {
        //?????????
    }
    

    bool changeI2CAddr (uint8_t addr)
    {
        uint8_t inputbuffer[6] = {0};
        uint8_t outputbuffer[9] = {0};
        inputbuffer[0] = CHANGE_I2C_ADDR;
        inputbuffer[1] = addr;
        protocol _protocol = pack(inputbuffer, sizeof(inputbuffer));
        writeI2C(ADDRESS, 0, (uint8_t *)&_protocol, sizeof(_protocol));
        //delay done in code. Is this necessary for us?
        readI2C(ADDRESS, 0, 9, outputbuffer);
       // sProtocol_t _protocol = pack(buf, sizeof(buf));
     //   writeData(0, (uint8_t *)&_protocol, sizeof(_protocol));
      //  delay(100);
      //  readData(0, recvbuf, 9);
        if (outputbuffer[8] != FucCheckSum(outputbuffer, 8))
            return 0;
        return outputbuffer[2];
    }


    float getVoltage(){

        uint8_t inputbuffer[6] = {0};
        uint8_t outputbuffer[9] = {0};
        inputbuffer[0] = GET_VOLTAGE;
        protocol _protocol = pack(inputbuffer, sizeof(inputbuffer));
        writeI2C(ADDRESS, 0, (uint8_t *)&_protocol, sizeof(_protocol));
        //delay done in code. Is this necessary for us?
        readI2C(ADDRESS, 0, 9, outputbuffer);
       // sProtocol_t _protocol = pack(buf, sizeof(buf));
     //   writeData(0, (uint8_t *)&_protocol, sizeof(_protocol));
      //  delay(100);
      //  readData(0, recvbuf, 9);
        if (outputbuffer[8] != FucCheckSum(outputbuffer, 8))
            return 0.0;
        return outputbuffer[2];
    }

    virtual float readGasConcPPM(uint8_t _temp)
    {//takes temp as a function of deg C
        return 0.0;
    }//For O2, No2, So2, O3, Cl2, divide by 10 

    virtual float readTempC()
    {
        return 0.0;
    }


    void changeTempComp()
    {
        if(tempComp == true) {tempComp = false;}
        else {tempComp == true;}
    }

    void dataToJSON(JsonObject js)
    {
        for (byte i=0; i < N_PARS; i++){
            js[PARAMETER_SHORT_NAMES[i]] = ((float)sampled_data[i] / 0xFFFF);
            
        };
    }


};
