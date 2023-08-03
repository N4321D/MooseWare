// BME Gas Sensor 

//#include <i2csensor.h>>

class BMESensor : public I2CSensor
{
    private:
    public:
        //const_array1 = [1,1,1,1,1,.99,1,.992,1,1,.998,.995,1,.99,1,1];
        //const_array2 = [8000000,4000000,2000000,1000000,499500.4995,248262.1648,125000,63004.03226,31281.28128,15625,7812.5,3906.25,1953.125,976.5625,488.28125,244.140625];
        //forcedmoderegister74 = 0x25;
        //put in stuff here unit?
        // int16_t sampled_data[2];
        //HUM_REG = 0x26;
        //TMP_REG = 0x23;
          float t_fine;
        bool startup = true;
        bool heatingUp;
        float sampled_data [4];//temporary solution
        unsigned long endtime;


    BMESensor(TwoWire &wire_in) : I2CSensor(wire_in)
    {
        //wire = &wire_in;
        strcpy(NAME, "BME680 Gas Resistance Sensor");
        strcpy(SHORT_NAME, "BME");
        ADDRESS = 0x77;
        N_PARS = 4;
        strcpy(PARAMETER_NAMES[0], "Resistance, KOhms");
        strcpy(PARAMETER_NAMES[1], "Temperature, deg C");
        strcpy(PARAMETER_NAMES[2], "Pressure, hPa");
        strcpy(PARAMETER_NAMES[3], "Humidity, %");
        strcpy(PARAMETER_SHORT_NAMES[0], "Res");
        strcpy(PARAMETER_SHORT_NAMES[1], "Temp");
        strcpy(PARAMETER_SHORT_NAMES[2], "Pres");
        strcpy(PARAMETER_SHORT_NAMES[3], "Hmd");



    }

    void init(){
        //Serial.println("checkpoint 1");
        if(startup){
            heatingUp = true;
            endtime = millis() + 15000; //15 second heat up time
            startup = false;
        }
        //Set hexadecimal values for Register 74 (controls osrs_t, osrs_p, and mode)
       // beginningregister74 = 0x24;
       
        //Set hexadecimal value for Register 72(XspiXXXosrs_h)
       // beginningregister72 = 0x1;

      //  target_temp = 300;
      //  amb_temp = 25;
      //  indices = [0xED, 0xEB, 0xEC, 0xEE, 0x02, 0x00];
      //  writeI2C(ADDRESS, 0x74, beginningregister74, 1);//Set up first time set up for the chip
       // writeI2C(ADDRESS, 0x72, beginningregister72, 1);
      //  writeI2C(ADDRESS, 0x64,0x59, 1) //Heating time of 100 ms
        
    }

    void sample(){
       // Serial.println("checkpoint 1.5");
        //if(!sgp.IAQmeasure()){Serial.println("Measure fail");}
       // Serial.println("checkpoint 2");
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
            endtime= millis() + 1000;
        }
       //  if (readI2C(ADDRESS, 0, 0, &sampled_data))
       // {
          //  error_count = 0;
       // }
       // else
      //  {
      //      error_count++;
      //  };
    }   


    float calcTempC(uint32_t temp_adc, float par_t1, float par_t2, float par_t3){
    	//float var1 = 0;
	   // float var2 = 0;
	   float calc_temp = 0;

	/* calculate var1 data */
	    //var1  = ((((float)temp_adc / 16384.0f) - ((float)par_t1 / 1024.0f))* ((float)par_t2));

	/* calculate var2 data */
	    //var2  = (((((float)temp_adc / 131072.0f) - ((float)par_t1 / 8192.0f)) * (((float)temp_adc / 131072.0f) - ((float)par_t1 / 8192.0f))) * ((float)par_t3 * 16.0f));

	/* t_fine value*/
	   //t_fine = (var1 + var2);

	/* compensated temperature data*/
	   // calc_temp  = ((t_fine) / 5120.0f);

	    return calc_temp;

    }

    float readGasConcPPM(uint16_t gas_res_adc, uint8_t gas_range){
	    float calc_gas_res = 0;
	    //float var1 = 0;
	    //float var2 = 0;
	    //float var3 = 0;

	   // const float lookup_k1_range[16] = {0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, -0.8,0.0, 0.0, -0.2, -0.5, 0.0, -1.0, 0.0, 0.0};
	   // const float lookup_k2_range[16] = {0.0, 0.0, 0.0, 0.0, 0.1, 0.7, 0.0, -0.8,-0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0}; ?????

	    //var1 = (1340.0f + (5.0f * dev->calib.range_sw_err));
	    //var2 = (var1) * (1.0f + lookup_k1_range[gas_range]/100.0f);
	    //var3 = 1.0f + (lookup_k2_range[gas_range]/100.0f);

	    //calc_gas_res = 1.0f / (float)(var3 * (0.000000125f) * (float)(1 << gas_range) * (((((float)gas_res_adc) - 512.0f)/var2) + 1.0f));

	    return calc_gas_res;
    }

    float readHumidity(){
        return 0.0;
    }

    float readRH(){
        return 0.0;
    }
    void dataToJSON(JsonObject js)
    {
        for (byte i=0; i < N_PARS; i++){
            js[PARAMETER_SHORT_NAMES[i]] = ((float)sampled_data[i]);
            
        };
    }

    void reset_procedure() //Note: NOT chpip specific
    {
        //Note this is a general call reset, which, according to the manufacturer's documentation, will work on any chip that supports this generic protocol
        //createInput(reset);
        //writeI2C(ADDRESS, reset, &input, sizeof(input));
    }

};