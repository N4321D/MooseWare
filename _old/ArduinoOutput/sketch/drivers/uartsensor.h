#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/20231109/MooseWare/arduino_firmware/RPI_Pico_driver/drivers/uartsensor.h"
//Generic protocol for UART serial communication. Should be included in all sensors that need or can use UART communication 
//built for raspberry pi pico on the second UART line (Serial1)
#include <Arduino.h>
#include "SoftwareSerial.h"
#include "HardwareSerial.h"

class UARTSensor

{
private:
    int32_t read_bytes; 
public:
    static const byte MAX_PARS = 16; // max pars for all sensors
    byte N_PARS = 3;                 // max pars for this sensor
    char NAME[32];                   // full name of sensor
    char SHORT_NAME[5];              // short name of sensor
    char PARAMETER_NAMES[MAX_PARS][16];      // name of parameters
    char PARAMETER_SHORT_NAMES[MAX_PARS][5]; // name of parameters
    uint error_count = 0;                    // count errors
    byte uart_error = 0;
    bool connected = true;                  // indicate if sensor is disconnected or not
    bool record = true;                     // indicate if sensor needs to be recorded or not

    String control_str;

    // sensor specific
    uint32_t sampled_data[MAX_PARS]; // data is stored here
    
    UARTSensor()
    {
        strcpy(NAME, "Sensor");
        strcpy(SHORT_NAME, "SENS");
        strcpy(PARAMETER_NAMES[0], "Parameter 1");
        strcpy(PARAMETER_NAMES[1], "Parameter 2");
        strcpy(PARAMETER_NAMES[2], "Parameter 3");
        strcpy(PARAMETER_SHORT_NAMES[0], "PAR1");
        strcpy(PARAMETER_SHORT_NAMES[1], "PAR2");
        strcpy(PARAMETER_SHORT_NAMES[2], "PAR3");
    }

    //Classes to write
    void setupSerial()
    {
        Serial1.begin(9600);
    }

    void test_connection()
    {
        if(Serial1.isListening())
        {
            connected = true;
        }
        else
            connected = false;

    }

    bool readUART(byte numBytes, T *data)
    {
        byte *byte_ptr = (byte *)data; // cast long int pointer to byte pointer
        if(Serial1.available() > 0)
        {
            for (int i = 0; i < numBytes; i++)
            {
                if (!reverse)
                {
                    byte_ptr[i] = Serial1.read();
                }
                else
                {
                    byte_ptr[numBytes - i - 1] = Serial1.read();
                };
            }
            return true;  
        }
        else
        {
            return false;
        }
    }

    bool writeUART()//is there a point to this? isnt this serial printing with extra steps
    {
        if(Serial1.available() > 0)
        {

            return true;
        }
        else
        {
            return false;
        }
    }



//generic classes for all base class sensors
    virtual void init() // virtual works as placeholder: e.g. if function is overwritten in subclass it calls subclass function
    {
        // call to initialize sensor with correct settings
    }

    virtual void trigger()
    {
        // trigger reading if nescessary
    }

    virtual void sample()
    {
        if (readI2C(ADDRESS, 0x22, 12, &sampled_data))
        {
            error_count = 0;
        }
        else
        {
            error_count++;
        };
    }

    void getSampledData(JsonObject js)
    {
        // called by loop
        if (i2c_error == 0)
            dataToJSON(js);
        else
            js["!I2C"] = i2c_error;
            dataToJSON(js);

    }

    void getInfo(JsonObject js)
    {
        js["name"] = NAME;
        // js["parameter_names"] = PARAMETER_NAMES;
        // js["parameter__short_names"] = PARAMETER_SHORT_NAMES;
        js["control_str"] = control_str;
        js["i2c_status"] = i2c_error;
        js["record"] = record;

        JsonArray par_names = js.createNestedArray("parameter_names");
        JsonArray par_short_names = js.createNestedArray("parameter_short_names");

        for (int i = 0; i < N_PARS; i++)
        {
            par_names.add(PARAMETER_NAMES[i]);
            par_short_names.add(PARAMETER_SHORT_NAMES[i]);
        }
    }

    virtual void dataToJSON(JsonObject js)
    {
        // write paraters in json object
        for (byte i = 0; i < N_PARS; i++)
        {
            js[PARAMETER_SHORT_NAMES[i]] = (float)sampled_data[i] / 2;
        };
    }

    // this function processes common functions for all chips
    // if the command is chip specific it is sent to the chip specific 
    // procCmd function
    void doCmd(const char *key, JsonVariant value){
        if (strcmp(key, "record") == 0){
            record = value.as<bool>();
        }
        else{
            procCmd(key, value);
            };

    }

    virtual void procCmd(const char *key, JsonVariant value)
    {
        // incoming commandands are processed here
        if (strcmp(key, "cmd1") == 0)
        {
            float test = value.as<float>();
        }
    }

    virtual void reset_procedure()
    {
        // overwrite with specific reset commands
    }

    virtual void stop()
    {
        // call stop things here
    }

    void reset()
    {
        // call to reset sensor, DO NOT OVERWRITE IN SUBCLASS
        uart_error = 0;

        reset_procedure();
        if (uart_error == 0)
            error_count = 0;
        //init();
    }


};