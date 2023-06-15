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

class I2CSensor
{
private:
    int32_t read_bytes;
    TwoWire *wire;

public:
    static const byte MAX_PARS = 16; // max pars for all sensors
    byte N_PARS = 3;                 // max pars for this sensor
    char NAME[32];                   // full name of sensor
    char SHORT_NAME[5];              // short name of sensor
    byte ADDRESS = 0x00;
    char PARAMETER_NAMES[MAX_PARS][16];      // name of parameters
    char PARAMETER_SHORT_NAMES[MAX_PARS][5]; // name of parameters
    uint error_count = 0;                    // count errors
    byte i2c_error = 0;
    bool connected = true;                  // indicate if sensor is disconnected or not
    bool record = true;                     // indicate if sensor needs to be recorded or not

    String control_str;

    // sensor specific
    uint32_t sampled_data[MAX_PARS]; // data is stored here

    I2CSensor(TwoWire &wire_in)
    {
        wire = &wire_in;
        strcpy(NAME, "Sensor");
        strcpy(SHORT_NAME, "SENS");
        strcpy(PARAMETER_NAMES[0], "Parameter 1");
        strcpy(PARAMETER_NAMES[1], "Parameter 2");
        strcpy(PARAMETER_NAMES[2], "Parameter 3");
        strcpy(PARAMETER_SHORT_NAMES[0], "PAR1");
        strcpy(PARAMETER_SHORT_NAMES[1], "PAR2");
        strcpy(PARAMETER_SHORT_NAMES[2], "PAR3");
    }

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

    /**
     * NOTE ADD THIS FUNCTION TO EACH SUBCLASS!!!
     */

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
            Serial.println(String(NAME) + ": test value received");
        }
    }

    void test_connection()
    {
        wire->beginTransmission(ADDRESS);
        i2c_error = wire->endTransmission();
        if (i2c_error > 0)
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
        i2c_error = wire->endTransmission();
        if (i2c_error > 0)
        {
            return false;
        };

        wire->requestFrom(address, numBytes, true);

        for (int i = 0; i < numBytes; i++)
        {
            if (!reverse)
            {
                byte_ptr[i] = wire->read();
            }
            else
            {
                byte_ptr[numBytes - i - 1] = wire->read();
            };
        }
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
        i2c_error = wire->endTransmission(); // TODO: this only writes the main class vars, how to access vars in subclasses?

        return (i2c_error == 0);
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
        i2c_error = 0;

        reset_procedure();
        if (i2c_error == 0)
            error_count = 0;
        //init();
    }
};
