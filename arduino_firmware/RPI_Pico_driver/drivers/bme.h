
// BME Gas Sensor 


#include <i2csensor.h>>

class BMEsensor : public I2CSensor
{
    private:
    public:
        const_array1 = [1,1,1,1,1,.99,1,.992,1,1,.998,.995,1,.99,1,1];
        const_array2 = [8000000,4000000,2000000,1000000,499500.4995,248262.1648,125000,63004.03226,31281.28128,15625,7812.5,3906.25,1953.125,976.5625,488.28125,244.140625];
        forcedmoderegister74 = 0x25;
        //put in stuff here unit?
        // int16_t sampled_data[2];
        HUM_REG = 0x26;
        TMP_REG = 0x23;
        float sampled_data [4];//temporary solution


    BMEsensor(TwoWire &wire_in) : GasSensor(wire_in)
    {
        strcpy(NAME, "BME680 Gas Resistance Sensor");
        strcopy(SHORT_NAME, "BME");
        ADDRESS = 0x77;
        N_PARS = 4;
        strcpy(PARAMETER_NAMES[0], "Resistance, Ohms");
        strcpy(PARAMETER_NAMES[1], "Temperature, deg C");
        strcpy(PARAMETER_NAMES[2], "Pressure, hPa");
        strcpy(PARAMETER_NAMES[3], "Humidity, %");
        strcpy(PARAMETER_SHORT_NAMES[0], "Res");
        strcpy(PARAMETER_SHORT_NAMES[1], "Temp");
        strcpy(PARAMETER_SHORT_NAMES[2], "Pres");
        strcpy(PARAMETER_SHORT_NAMES[3], "Hmd");



    }

    void init(){
        //Set hexadecimal values for Register 74 (controls osrs_t, osrs_p, and mode)
        beginningregister74 = 0x24;
       
        //Set hexadecimal value for Register 72(XspiXXXosrs_h)
        beginningregister72 = 0x1;

        target_temp = 300;
        amb_temp = 25;
        indices = [0xED, 0xEB, 0xEC, 0xEE, 0x02, 0x00];
        writeI2C(ADDRESS, 0x74, beginningregister74, 1);//Set up first time set up for the chip
        writeI2C(ADDRESS, 0x72, beginningregister72, 1);
        writeI2C(ADDRESS, 0x64,0x59, 1) //Heating time of 100 ms
        
    }

    void sample(){
         if (readI2C(ADDRESS, 0, 0, &sampled_data))
        {
            error_count = 0;
        }
        else
        {
            error_count++;
        };
    }   


    float calcTempC(){
        var1 = (temp_adc >> 3) - (par_t1 << 1)
        var2 = (var1 * par_t2) >> 11
        var3 = ((var1 >> 1) * (var1 >> 1)) >> 12
        var3 = ((var3) * (par_t3 << 4)) >> 14
        t_fine = var2 + var3 # + int(math.copysign((((int(abs(120.85) * 100)) << 8) - 128) / 5, 120.85))
        calc_temp = (((t_fine * 5) + 128) >> 8)
        if calc_temp < 0:
            calc_temp = (1 << 32) + calc_temp
        return calc_temp
    }

    float readGasConcPPM(){

    }

    float readHumidity(){

    }

    float readRH(){
        
    }

    };