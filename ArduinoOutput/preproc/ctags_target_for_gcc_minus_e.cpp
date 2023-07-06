# 1 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino"
// NOTES:
// - RPI pico has 2 i2c controllers 0 (wire) and 1 (wire1), they can only use specific
//    ports, refer to pinout which one can use __itimer_which
//    if mixed up it will crash
//  - I2C error codes are return as negative values in status, error codes are:
//        0: success.
//        -1: data too long to fit in transmit buffer.
//        -2: received NACK on transmit of address.
//        -3: received NACK on transmit of data.
//        -4: other error.
//        -5: timeout
//        -0x7F: other error

# 15 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2
# 16 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2


# 19 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2

// display
# 22 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2






Adafruit_SSD1306 display(128 /* OLED display width, in pixels*/, 64 /* OLED display height, in pixels*/, &Wire, -1 /* Reset pin # (or -1 if sharing Arduino reset pin)*/);

// interrupt timer libs:
# 32 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2
# 33 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2

struct adjustableSettings
{
  // struct with adjustable settings
  byte sample_analog = 0; // set bit [0 - 3] to sample analogue channel
  float timer_freq_hz = 256; // 2048.0;      // timer freq in Hz (start freq)
  float current_timer_freq_hz = 0; // actual timer freq
  float min_freq_hz = 1.0; // minimal sample frequency in Hz
  float idle_freq_hz = 2.0; // 2048.0;      // timer freq in Hz (start freq)
  uint loops_before_adjust = 0; // number of loops too slow or fast before adjusting (is set in set freq)
  const float TIME_SEC_BEFORE_ADJUST = 1; // time in seconds before adjusting sample f, change here to set
};

struct textStr
{
  // struct with all text things
  const char *idle = "Standby...";
  const char *rec = "Recording...";
  const char *defaultName = "RPI - Pico";
};

textStr texts;

adjustableSettings settings;

// declare json for data in and out

char jsonString_out[10 * 1024U];

DynamicJsonDocument doc_out(10 * 1024U);
DynamicJsonDocument doc_in(10 * 1024U);

// // init sensors
# 67 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2
# 68 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2
# 69 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2
# 70 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2

static OISSensor oissensor(Wire1);
static MOTSensor motsensor(Wire1);
static PInSensor pinsensor(Wire1);
// create sensor array
static I2CSensor *ptrSensors[] = {&oissensor, &motsensor, &pinsensor};

// for sampling
uint callCounter = 0; // counts the number of calls to ImterHandler by interupt clock
uint loopCounter = 0; // counts the number of finished loop calls
uint loopBehind = 0; // difference between callCoutner & loopCounter

unsigned long loopStart = 0; // timepoint of start of loop
unsigned long lastLoop = 0; // start time of last loop
unsigned long startTime = 0; // start of recording in micros

unsigned long dt = 0; // duration of loop
unsigned long sampleDT = 0; // time needed to sample sensors

bool START = false;

char NAME[32];

# 94 "/home/dmitri/Documents/Work/Coding/App/0_0_Recording_Apps/rec_app/arduino_firmware/RPI_Pico_driver/RPI_Pico_driver.ino" 2

// Init RPI_PICO_Timer
RPI_PICO_Timer ITimer(0);

bool TimerHandler(repeating_timer *rt)
{ // this function is called by the interupt timer
  callCounter++;
  // do something here
  return true; // return true to keep repeating, false to stop
}

void setLed(int state = -1)
{
  // blink led
  // state is 0 for off, 1 for on or -1 to toggle
  digitalWrite((25u), !digitalRead((25u)));
}

void displayText(String txt = "text here",
                 uint8_t x = 0,
                 uint8_t y = 0,
                 uint8_t size = 1,
                 bool clear_line = true,
                 bool clear_all = false)
{
  if (clear_line)
    display.fillRect(x, y, 128, 10, 0 /*|< Draw 'off' pixels*/ /*|< Draw 'off' pixels*/);
  if (clear_all)
    display.clearDisplay();
  if (size != 1)
    display.setTextSize(1); // Normal 1:1 pixel scale

  display.setTextColor(1 /*|< Draw 'on' pixels*/); // Draw white text
  display.setCursor(x, y);
  display.println(txt);
  display.display();
};

void feedback(String txt,
              uint8_t x = 5,
              uint8_t y = 30,
              bool over_serial = false)
{
  if (over_serial)
    Serial.println(txt);

  displayText(txt, x, y, 1, true, false);
}

void feedbackstats(const char *txt)
{
  Serial.println(txt);
  char buf[21]; // 10 characters + NUL
  sprintf(buf, "%20s", txt); // Right-justified message
  displayText(buf, 5, 0, 1, true, false);
}

void adjustFreq(float freq)
{
  if ((!(settings.min_freq_hz <= freq <= settings.timer_freq_hz)) || (freq == settings.current_timer_freq_hz))
    return;

  // Interval in unsigned long microseconds
  if (ITimer.attachInterrupt(freq, TimerHandler))
  {
    char txt[16];
    sprintf(txt, "%.1f Hz", freq);
    feedbackstats(txt);
    if (freq > 10)
      settings.loops_before_adjust = settings.TIME_SEC_BEFORE_ADJUST * freq;
    else
      settings.loops_before_adjust = 10;
  }

  else
    feedback("Err setting Freq");
  settings.current_timer_freq_hz = freq;
  loopCounter = callCounter;
}

byte findSensByName(const char *name)
{
  // returns index of sensor with short name matching input name
  for (byte i = 0; i < sizeof(ptrSensors) / sizeof(ptrSensors[0]); i++)
  {
    if (strcmp(name, ptrSensors[i]->SHORT_NAME) == 0)
    {
      return i;
    }
  }
  Serial.println(String(name) + " not found in sensor list");
  return 0xFF;
}

void sample()
{
  doc_out.clear();

  doc_out["us"] = loopStart - startTime;
  doc_out["sDt"] = sampleDT;

  // trigger sensors (RESET if needed)
  for (byte i = 0; i < sizeof(ptrSensors) / sizeof(ptrSensors[0]); i++)
  {
    if (!ptrSensors[i]->connected || !ptrSensors[i]->record)
      continue;

    // reset if needed
    if (ptrSensors[i]->error_count) //> settings.loops_before_adjust / 10
    {
      ptrSensors[i]->reset();
      ptrSensors[i]->init(); // do not put in driver, does not work for some reason..
    }

    ptrSensors[i]->trigger();
  };

  // sample sensors
  for (byte i = 0; i < sizeof(ptrSensors) / sizeof(ptrSensors[0]); i++)
  {
    if (!ptrSensors[i]->connected || !ptrSensors[i]->record)
      // skip sensor if not connected or record is set to false
      continue;

    ptrSensors[i]->sample();

    JsonObject sens_json = doc_out.createNestedObject(ptrSensors[i]->SHORT_NAME);

    ptrSensors[i]->getSampledData(sens_json);
  }

  // read analog data
  // TODO: this can be more efficient with dma; write seperate driver for analog
  if (settings.sample_analog & (1 << 0))
    doc_out["A0"] = analogRead(A0);
  if (settings.sample_analog & (1 << 1))
    doc_out["A1"] = analogRead(A1);
  if (settings.sample_analog & (1 << 2))
    doc_out["A2"] = analogRead(A2);
}

void idle()
{
  // idle loop, check connected sensors etc
  if (settings.current_timer_freq_hz != settings.idle_freq_hz)
    adjustFreq(settings.idle_freq_hz);

  feedback(texts.idle);

  // send setup pars
  doc_out.clear();
  doc_out["idle"] = true;
  JsonObject sens_json = doc_out.createNestedObject("CTRL");
  sens_json["name"] = NAME;
  sendData();

  // test connected sensors
  for (byte i = 0; i < sizeof(ptrSensors) / sizeof(ptrSensors[0]); i++)
  {
    doc_out.clear();
    doc_out["idle"] = true;
    ptrSensors[i]->test_connection();
    JsonObject sens_json = doc_out.createNestedObject(ptrSensors[i]->SHORT_NAME);
    ptrSensors[i]->getInfo(sens_json);
    sendData();
  };
  delay(100);
}

void run()
{
  feedback(texts.rec);
  // init sensors
  for (byte i = 0; i < sizeof(ptrSensors) / sizeof(ptrSensors[0]); i++)
  {
    ptrSensors[i]->init();
  }
  adjustFreq(settings.timer_freq_hz);
}

void procCmd(const char *key, JsonVariant jsonVal)
{
  // process command
  if (jsonVal.is<JsonObject>())
  {
    JsonObject value = jsonVal.as<JsonObject>();

    for (JsonPair kv : value)
    {
      if (strcmp(key, "CTRL") == 0)
      {
        control(kv.key().c_str(), kv.value());
      }
      else
      {
        byte sens_idx = findSensByName(key);
        if (sens_idx < 0xff)
        {
          ptrSensors[sens_idx]->doCmd(kv.key().c_str(), kv.value());
        };
      }
    };
    //
  }
  else
  {
    Serial.println("unknow object");
  };
}

void control(const char *key, JsonVariant value)
{
  // device control functions

  // set recording frequency:
  if (strcmp(key, "freq") == 0)
  {
    float freq = value.as<float>();
    settings.timer_freq_hz = freq;
    adjustFreq(freq);
  }

  if (strcmp(key, "run") == 0)
  {
    START = value.as<bool>();
    START ? run() : idle();
  }
  if (strcmp(key, "name") == 0)
  {
    // strcpy(NAME, value.as<const char*>());
    // feedback(NAME, 5, 20);
    setName(value.as<const char *>());
  }
}

void setName(const char *name)
{
  strcpy(NAME, name);
  feedback(NAME, 5, 20);
  // Save the name to EEPROM
  EEPROM.put(0, NAME);
  EEPROM.commit();
};

void loadName(){
  // Saved data
  char loadedData[sizeof(NAME)];
  EEPROM.begin(sizeof(NAME));
  EEPROM.get(0, loadedData);

  // Check if the loaded data is empty or uninitialized
  bool isEmpty = true;
  for (int i = 0; i < sizeof(NAME); i++)
  {
    if (loadedData[i] != '\0')
    {
      isEmpty = false;
      break;
    }
  }

  // Use the loaded data if not empty, otherwise use the default value
  setName(isEmpty ? texts.defaultName : loadedData);
};

void readInput()
{
  // read data from serial
  while (Serial.available())
  { // Parse the JSON object
    DeserializationError error = deserializeJson(doc_in,
                                                 Serial.readStringUntil('\n'));

    // If parsing succeeds, do stuff here
    if (!error)
    { // do stuff here
      JsonObject root = doc_in.as<JsonObject>();
      for (JsonPair kv : root)
      {
        procCmd(kv.key().c_str(),
                kv.value());
      }
    }
    else
    {
      Serial.println("deserialization error on input");
    };
  }
}

void sendData()
{
  // Serialize the JSON object to a string
  serializeJson(doc_out, jsonString_out);

  // Send the JSON object over USB serial
  Serial.println(jsonString_out);
}

void setup()
{
  pinMode((25u), OUTPUT);
  setLed(1);

  settings.sample_analog = (0 << 0) | (0 << 1) | (0 << 2);

  // i2c display
  Wire.setSDA(0); // Add these lines
  Wire.setSCL(1); //
  Wire.begin(); //
  Wire.setClock(400000); // i2c clockspeed (call after begin)
  Wire.setTimeout(1);

  Serial.begin(4000000);
  Serial.setTimeout(0); // set serial timeout in ms

  // SSD1306_SWITCHCAPVCC = generate display voltage from 3.3V internally
  if (!display.begin(0x02 /*|< Gen. display voltage from 3.3V*/, 0x3C /* See datasheet for Address; 0x3C*/))
  {
    Serial.println((reinterpret_cast<const __FlashStringHelper *>(("Display not connected: SSD1306 allocation failed"))));
  }
  display.clearDisplay();

  feedback("Waiting for Serial");

  while (!Serial)
  {
    feedback("Waiting for Serial");
    delay(10);
  }; // wait for serial
  Serial.println(welcome_text);

  loadName();

  feedback("setting up i2c");
  // NOTE: pico has 2 i2c controllers 1 and 2 check which one can use which pins!!
  Wire1.setSDA(2);
  Wire1.setSCL(3);
  Wire1.begin();
  Wire1.setClock(400000); // i2c clockspeed (call after begin)
  Wire1.setTimeout(1); // timeout in us

  // analog
  // analogReference(DEFAULT); // set the reference voltage to 3.3V
  analogReadResolution(12); // set the resolution to 12 bits (0-4095)

  adjustFreq(settings.idle_freq_hz);

  startTime = micros();
  loopCounter = callCounter - 1;
}

void loop()
{
  if (!Serial)
  { // connection lost
    setLed(1);
    feedback("Serial Disconnected");
    // stop recording
    START = 0;
    idle();
    while (!Serial)
    {
      loopCounter = callCounter;
    }
    feedback("Recording...");
  }

  // read input data
  readInput();

  loopBehind = callCounter - loopCounter;

  if (loopBehind == 0)
    // interupt timer was not called yet
    return;

  loopStart = micros();
  loopCounter++;

  if (!START)
  {
    // not ready to record
    idle();
    return;
  }

  // sample here:
  sample();
  sampleDT = micros() - loopStart;

  // send data over serial
  sendData();

  if (callCounter % ((uint)settings.current_timer_freq_hz / 2) == 0)
  {
    // do every second
    setLed();
  }

  if (loopBehind > settings.loops_before_adjust)
  {
    // reduce sample speed
    adjustFreq(settings.current_timer_freq_hz / 2.0);
    loopCounter = callCounter;
  }
  if (settings.current_timer_freq_hz < settings.timer_freq_hz)
  {
  }
  lastLoop = loopStart;

  dt = micros() - loopStart;

  // increase speed if ahead
  if ((1000000 / (dt + 10)) > (settings.current_timer_freq_hz * 2))
  {
    if ((settings.current_timer_freq_hz * 2) <= settings.timer_freq_hz)
    {
      static uint increase_counter = 0;
      increase_counter++;
      if (increase_counter % settings.loops_before_adjust == 0)
        adjustFreq(settings.current_timer_freq_hz * 2);
    }
  }
}

// TODO: Ensure that init is called when sensor has power again  (e.g. there is no i2c error but init was not called before)
