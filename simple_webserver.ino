#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>

void send_data();
void adjust_setpoint();

#define ONE_WIRE_BUS 2
#define PUMP_CONTROL 0
#define integral_windup_lim 50
#define equilibrium_constant 400

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
ESP8266WebServer server;

char* NETWORK_ID = "vodafoneB1100A";
char* PASSWORD = "@leadership room 11";
double temp;
float sum_error = 0;
float setpoint = 25;
int kp = 10;
int ki = 1.25;
long start_time;

void setup()
{
    WiFi.begin(NETWORK_ID, PASSWORD);
    Serial.begin(115200);
    sensors.begin();
    while (WiFi.status() != WL_CONNECTED) {
        Serial.print(".");
        delay(500);
    }
    Serial.println("");
    Serial.print("IP address: ");
    Serial.print(WiFi.localIP());

    start_time = millis();
    pinMode(PUMP_CONTROL, OUTPUT);
    analogWrite(PUMP_CONTROL, 0);

    server.on("/connect", [](){server.send(200, "text/plain", "");});
    server.on("/request_data", send_data);
    server.on("/adjust_setpoint", adjust_setpoint);
    server.begin();
}

void loop()
{
    sensors.requestTemperatures();
    temp = sensors.getTempCByIndex(0);
    server.handleClient();
    control_loop();
}

void send_data()
{
  char outbuffer[200];
  DynamicJsonBuffer jBuffer;
  JsonObject &root = jBuffer.createObject();
  root["Temp"] = temp;
  root["Runtime"] = millis() - start_time;
  root["Setpoint"] = setpoint;
  root["Element status"] = "ON";
  root.printTo(outbuffer, root.measureLength() + 1);
  server.send(200, "text/plain", outbuffer);
}

void adjust_setpoint()
{
    String data = server.arg("plain");
    StaticJsonBuffer<200> jBuffer;
    JsonObject &jObject = jBuffer.parseObject(data);
    String value = jObject["value"];
    setpoint = value.toInt();
    server.send(204, "");
}

void control_loop()
{
    // PI controller
    int test = millis();
    float error = temp - setpoint;
    sum_error += error;
    if (sum_error < -integral_windup_lim) {
        sum_error = -integral_windup_lim;
    } else if (sum_error > integral_windup_lim) {
        sum_error = integral_windup_lim;
    }

    int output = kp * error + ki * sum_error + equilibrium_constant;
    if (output < 0) {
        output = 0;
    } else if (output > 1024) {
        output = 1024;
    }
    analogWrite(PUMP_CONTROL, output);
    Serial.println(millis() - test);
}
