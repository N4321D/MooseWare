#line 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/drivers/i2csensor.h"
/**
*  template for sensor class

* to subclass make a new sensor parameters, example:
* #include "i2csensor.h"

* template <byte N>
* struct OISParameters
* {
*     static constexpr char name[] = "OIS";       // full name of sensor
*     static constexpr char short_name[] = "OIS"; // short name of sensor
*     static const byte address = 0x5B;
*     uint32_t sampled_data[N];                                                       // data is stored here
*     const char *parameter_names[N] = {"Parameter 1", "Parameter 1", "Parameter 1"}; // name of parameters
*     const char *parameter_short_names[N] = {"PAR1", "PAR2", "PAR3"};                // name of parameters
*     const byte sample_regs[N] = {0xF, 0xF, 0xF};                                    // registers to sample per parameter
*     const byte no_bytes[N] = {1, 1, 1};                                             // number of bytes to sample per registery
*     uint error_count = 0;                                                           // count errors
*     byte i2c_error = 0;                                                             // i2c error no if any
* };

* class OISSensor : public I2CSensor
* {
* private:
*     OISParameters<3> vars;

* public:
*     OISSensor(TwoWire &wire_in) : I2CSensor(wire_in)
*     {
*     }

*     OISParameters<3> getData()
*     {
*         return vars;
*     }
* };
*/

#include <Wire.h>
#include <Arduino.h>

class Sensor
{
private:

public:
    static const byte MAX_PARS = 32; // max pars for all sensors
    uint32_t sampled_data[MAX_PARS]; // data is stored here
    byte N_PARS = 3;                 // max pars for this sensor
    char NAME[32];                   // full name of sensor
    char SHORT_NAME[5];              // short name of sensor
    char PARAMETER_NAMES[MAX_PARS][16];      // name of parameters
    char PARAMETER_SHORT_NAMES[MAX_PARS][5]; // name of parameters
    uint error_count = 0;                    // count errors
    int8_t STATUS = 0;      // current status
    int8_t SENT_STATUS = 0; // status that was last reported
    bool connected = true;  // indicate if sensor is disconnected or not
    bool record = true;     // indicate if sensor needs to be recorded or not
    byte zero_count = 0;        // count zeros -> if multiple zeroes in a row, reset (only use for specific sensors)
    byte zeros_treshold = 0;    // set to 0 to not reset, else sensor is resetted if zero_count > zeros_theshold

    String control_str;

    Sensor(){
        // example code:
        // strcpy(NAME, "Sensor");
        // strcpy(SHORT_NAME, "SENS");
        // strcpy(PARAMETER_NAMES[0], "Parameter 1");
        // strcpy(PARAMETER_NAMES[1], "Parameter 2");
        // strcpy(PARAMETER_NAMES[2], "Parameter 3");
        // strcpy(PARAMETER_SHORT_NAMES[0], "PAR1");
        // strcpy(PARAMETER_SHORT_NAMES[1], "PAR2");
        // strcpy(PARAMETER_SHORT_NAMES[2], "PAR3");
    };

    void check_and_trigger()
    {
        if (error_count || (zeros_treshold && (zero_count > zeros_treshold)))
            reset();
        trigger();
    };

    // this function processes common functions for all chips
    // if the command is chip specific it is sent to the chip specific
    // procCmd function
    void doCmd(const char *key, JsonVariant value)
    {
        if (strcmp(key, "record") == 0)
        {
            record = value.as<bool>();
        }
        else
        {
            procCmd(key, value);
        };
    };
   
    void getInfo(JsonObject js)
    {
        js["name"] = NAME;
        js["control_str"] = control_str;
        js["#ST"] = STATUS;
        SENT_STATUS = STATUS;
        js["record"] = record;

        JsonArray par_names = js.createNestedArray("parameter_names");
        JsonArray par_short_names = js.createNestedArray("parameter_short_names");

        for (int i = 0; i < N_PARS; i++)
        {
            par_names.add(PARAMETER_NAMES[i]);
            par_short_names.add(PARAMETER_SHORT_NAMES[i]);
        }
    };

    void getSampledData(JsonObject js)
    {
        // called by loop
        // if (STATUS >= 0)
        //     dataToJSON(js);
        if (STATUS != SENT_STATUS || STATUS < 0)
        {
            js["#ST"] = STATUS;
            SENT_STATUS = STATUS;
        };
        dataToJSON(js);
    };
    
    void reset()
    {
        // call to reset sensor, DO NOT OVERWRITE IN SUBCLASS
        STATUS = 0;
        zero_count = 0; // reset zero count
        error_count = 0;
        reset_procedure();
        init();
    };

    // VIRTUAL METHODS
    virtual void init() // virtual works as placeholder: e.g. if function is overwritten in subclass it calls subclass function
    {
        // call to initialize sensor with correct settings
    };

    virtual void trigger()
    {
        // trigger reading if nescessary
    };

    virtual void sample()
    {
        /**
         * Sample data here and store in some local variable such as sampled data
         * tranfer to json object later in dataToJSON
        */
        // if (readI2C(ADDRESS, 0x22, 12, &sampled_data))
        // {
        //     error_count = 0;
        // }
        // else
        // {
        //     error_count++;
        // };
    };

    virtual void dataToJSON(JsonObject js)
    {    /**
         * fill Json object with recorded data in this function
         * - js: json object
        */
        // Example:
        // for (byte i = 0; i < N_PARS; i++)
        // {
        //     js[PARAMETER_SHORT_NAMES[i]] = (float)sampled_data[i] / 2;
        // };
    };

    virtual void procCmd(const char *key, JsonVariant value)
    {   /**
        * process incoming commands here
        */
        // Example:
        // if (strcmp(key, "cmd1") == 0)
        // {
        //     float test = value.as<float>();
        // }
    };

    virtual void test_connection()
    {
        /**
         * test connection here to see if bus / sensors are available
        */
        STATUS = 0; // reset status
        // Connection test here
        if (STATUS < 0)
            connected = false;
        else
            connected = true;
    };

    virtual void reset_procedure()
    {
        // overwrite with specific reset commands
    };

    virtual void stop()
    {
        // call stop things here
    };


};


class I2CSensor : public Sensor
{
private:
    TwoWire *wire;

public:
    // I2C Sensor specific    
    byte ADDRESS = 0x00;

    // sensor specific
    byte zeros_treshold = 0xfd; // set to 0 to not reset, else sensor is resetted if zero_count > zeros_theshold

    I2CSensor(TwoWire &wire_in)
    {
        wire = &wire_in;

    }

    void test_connection()
    {
        STATUS = 0; // reset status
        wire->beginTransmission(ADDRESS);
        STATUS = -wire->endTransmission();
        if (STATUS < 0)
            connected = false;
        else
            connected = true;
    }

    /**
     * Read bytes from an I2C device register.
     *
     * @param reg The register address to read from.
     * @param numBytes The number of bytes to read.
     * @param data A pointer to the memory where the read bytes will be stored.
     * @param reverse The byte order in which the data should be read (optional).
     * @return True if the read was successful, false otherwise.
     */
    template <typename T>
    bool readI2C(byte address, byte reg, byte numBytes, T *data, bool reverse = false)
    {                                  // send register address to sensor
        byte *byte_ptr = (byte *)data; // cast long int pointer to byte pointer
        wire->beginTransmission(address);
        wire->write(reg);
        byte _err = wire->endTransmission();

        byte _n_zeros = 0;

        if (_err > 0)
        {
            STATUS = -_err;
            return false;
        };

        wire->requestFrom(address, numBytes, true);

        for (int i = 0; i < numBytes; i++)
        {
            if (!reverse)
            {
                byte_ptr[i] = wire->read();
                if (byte_ptr[i] == 0)
                {
                    _n_zeros++;
                };
            }
            else
            {
                byte_ptr[numBytes - i - 1] = wire->read();
                if (byte_ptr[numBytes - i - 1] == 0)
                {
                    _n_zeros++;
                };
            };
        }
        if (STATUS < 0 && _err == 0)
            STATUS = 0;
        if (_n_zeros == numBytes)
            zero_count++;
        return true;
    }

    /**
     * Write an array of bytes to a specified register of the I2C sensor.
     *
     * @param reg The register address to write to.
     * @param data A pointer to the data to write.
     * @param numBytes The number of bytes to write.
     * @return true if the write was successful, otherwise false the error code is saved as vars.i2cerror
     */
    bool writeI2C(byte address, byte reg, const byte *data, byte numBytes)
    {
        wire->beginTransmission(address);
        wire->write(reg); // specify the register to write to

        for (int i = 0; i < numBytes; i++)
        {
            wire->write(data[i]); // write each byte to the register
        }
        byte _err = wire->endTransmission();
        if (_err > 0)
            STATUS = -_err;
        if (STATUS < 0 && _err == 0)
            STATUS = 0;
        return (_err == 0);
    }

};
