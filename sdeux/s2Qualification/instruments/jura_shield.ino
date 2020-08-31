
/*---------- JURA Shield ---------------*/
/*Joint Utilitary Relay Activation board*/
/****************************************/
/* Author: Jonathan Braun - Oct. 2018   */
/* Alpes-Lasers SA                      */
/****************************************/

// GPIO Definition

// Convenience
#define TRUE 1
#define FALSE 0

// Debounce

#define DEBOUNCE 250

// Commands

#define IN_ARM_ON 20
#define IN_SAFETY_ON 21
#define MCU_OUT_INT_ON 22
#define INTERLOCK_ON 23
#define IN_MOD_DIR_ON 24
#define GND_ON 25
#define IN_ARM_OFF 26
#define IN_SAFETY_OFF 27
#define MCU_OUT_INT_OFF 28
#define INTERLOCK_OFF 29
#define IN_MOD_DIR_OFF 30
#define GND_OFF 31

// Relays
#define IN_ARM 2
#define IN_SAFETY 3
#define MCU_OUT_INT 4
#define INTERLOCK 5
#define IN_MOD_DIR 6
#define GND 7

// Buttons

#define B_IN_ARM 8
#define B_IN_SAFETY 12
#define B_MCU_OUT_INT 13
#define B_INTERLOCK 11
#define B_IN_MOD_DIR 9
#define B_GND 10

// Global variables

// Debounce
//byte buttons[] = {B_IN_ARM,B_IN_SAFETY,B_MCU_OUT_INT,B_INTERLOCK,B_IN_MOD_DIR,B_GND};
//#define NUMBUTTONS sizeof(buttons)
//volatile byte pressed[NUMBUTTONS],justPressed[NUMBUTTONS],justReleased[NUMBUTTONS],lastPressed[NUMBUTTONS];
int locked = 0;
int active = 0;
long int lockTime = 0;

// Commands
String command = "";
int receivedCommand;
int serialReceived = FALSE;

void setup() 
{
  //GPIO Setup

  // Relays
  pinMode(IN_ARM,OUTPUT);
  pinMode(IN_SAFETY,OUTPUT);
  pinMode(MCU_OUT_INT,OUTPUT);
  pinMode(INTERLOCK,OUTPUT);
  pinMode(IN_MOD_DIR,OUTPUT);
  pinMode(GND,OUTPUT);

  // Buttons
  pinMode(B_IN_ARM,INPUT_PULLUP);
  pinMode(B_IN_SAFETY,INPUT_PULLUP);
  pinMode(B_MCU_OUT_INT,INPUT_PULLUP);
  pinMode(B_INTERLOCK,INPUT_PULLUP);
  pinMode(B_IN_MOD_DIR,INPUT_PULLUP);
  pinMode(B_GND,INPUT_PULLUP);

  // Serial
  Serial.begin(9600);
  Serial.println("Connection to JURA shield established");
}

void loop() {

   //Serial Read
  while(Serial.available())
  {   
      serialReceived = TRUE;
      //command = "";
      delay(30);  //delay to allow buffer to fill 
      if (Serial.available() >0)
      {
        char c = Serial.read();  //gets one byte from serial buffer
        command += c; //makes the string readString
      };
  }

  if(serialReceived)
  {
      Serial.print("Command string: ");
      Serial.println(command);
      receivedCommand = translateCommand(command);
      Serial.print("Command int: ");
      Serial.println(receivedCommand);
      if((receivedCommand != IN_ARM_ON) &&
       (receivedCommand != IN_SAFETY_ON) &&
       (receivedCommand != MCU_OUT_INT_ON) &&
       (receivedCommand != INTERLOCK_ON) &&
       (receivedCommand != IN_MOD_DIR_ON) &&
       (receivedCommand != GND_ON) &&
       (receivedCommand != IN_ARM_OFF) &&
       (receivedCommand != IN_SAFETY_OFF) &&
       (receivedCommand != MCU_OUT_INT_OFF) &&
       (receivedCommand != INTERLOCK_OFF) &&
       (receivedCommand != IN_MOD_DIR_OFF) &&
       (receivedCommand != GND_OFF))
       {
        digitalWrite(IN_ARM,LOW);
        digitalWrite(IN_SAFETY,LOW);
        digitalWrite(MCU_OUT_INT,LOW);
        digitalWrite(INTERLOCK,LOW);
        digitalWrite(IN_MOD_DIR,LOW);
        digitalWrite(GND,LOW);    
      }
      else
      {
        switch(receivedCommand)
        {
          case IN_ARM_ON:
            digitalWrite(IN_ARM,HIGH);
            active = B_IN_ARM; 
          break;
          case IN_ARM_OFF:
            digitalWrite(IN_ARM,LOW);
            active = 99;
          break;
          case IN_SAFETY_ON:
            digitalWrite(IN_SAFETY,HIGH);
            active = B_IN_SAFETY;
          break;
          case IN_SAFETY_OFF:
            digitalWrite(IN_SAFETY,LOW);
            active = 99;
          break;
          case MCU_OUT_INT_ON:
            digitalWrite(MCU_OUT_INT,HIGH);
            active = B_MCU_OUT_INT;
          break;
          case MCU_OUT_INT_OFF:
            digitalWrite(MCU_OUT_INT,LOW);
            active = 99;
          break;
          case INTERLOCK_ON:
            digitalWrite(INTERLOCK,HIGH);
            active = B_INTERLOCK;
          break;
          case INTERLOCK_OFF:
            digitalWrite(INTERLOCK,LOW);
            active = 99;
          break;
          case IN_MOD_DIR_ON:
            digitalWrite(IN_MOD_DIR,HIGH);
            active = B_IN_MOD_DIR;
          break;
          case IN_MOD_DIR_OFF:
            digitalWrite(IN_MOD_DIR,LOW);
            active = 99;
          break;
          case GND_ON:
            digitalWrite(GND,HIGH);
            active = B_GND;
          break;
          case GND_OFF:
            digitalWrite(GND,LOW);
            active = 99;
          break;
          default:
            digitalWrite(IN_ARM,LOW);
            digitalWrite(IN_SAFETY,LOW);
            digitalWrite(MCU_OUT_INT,LOW);
            digitalWrite(INTERLOCK,LOW);
            digitalWrite(IN_MOD_DIR,LOW);
            digitalWrite(GND,LOW);
          break;
        }
      }
      command = "";
      serialReceived = FALSE;
  }
  
  if(digitalRead(active))
  {
    if(locked)
    {
      if(millis() >= (lockTime+DEBOUNCE))
      {
        locked = FALSE;
        lockTime = 0;
        Serial.println("Unlocked");
      }
    }
    else
    {
      checkButtons();
    }
  }
}


//************** Functions ******************

int translateCommand(String command)
{
  if(command == "IN_ARM_ON\n")
    return IN_ARM_ON;  
  if(command == "IN_SAFETY_ON\n")
    return IN_SAFETY_ON;
  if(command == "MCU_OUT_INT_ON\n")
    return MCU_OUT_INT_ON;
  if(command == "INTERLOCK_ON\n")
    return INTERLOCK_ON;
  if(command == "IN_MOD_DIR_ON\n")
    return IN_MOD_DIR_ON;
  if(command == "GND_ON\n")
    return GND_ON;
  if(command == "IN_ARM_OFF\n")
    return IN_ARM_OFF;
  if(command == "IN_SAFETY_OFF\n")
    return IN_SAFETY_OFF;
  if(command == "MCU_OUT_INT_OFF\n")
    return MCU_OUT_INT_OFF;
  if(command == "INTERLOCK_OFF\n")
    return INTERLOCK_OFF;
  if(command == "IN_MOD_DIR_OFF\n")
    return IN_MOD_DIR_OFF;
  if(command == "GND_OFF\n")
    return GND_OFF;
}

void checkButtons()
{
  int pressed = 0;
  for (int i=8;i<=13;i++)
  {
      if(!digitalRead(i))
      {
        locked = TRUE;
        lockTime = millis();
        pressed = i;
        Serial.print("Pressed: ");
        Serial.println(pressed);
        Serial.println("Locked");
      
  
      if (pressed == active)
      {
        digitalWrite(IN_ARM,LOW);
        digitalWrite(IN_SAFETY,LOW);
        digitalWrite(MCU_OUT_INT,LOW);
        digitalWrite(INTERLOCK,LOW);
        digitalWrite(IN_MOD_DIR,LOW);
        digitalWrite(GND,LOW);
        active = 99; //Has to be different from zero, not very elegant
    
      }
      else
      {
        digitalWrite(IN_ARM,LOW);
        digitalWrite(IN_SAFETY,LOW);
        digitalWrite(MCU_OUT_INT,LOW);
        digitalWrite(INTERLOCK,LOW);
        digitalWrite(IN_MOD_DIR,LOW);
        digitalWrite(GND,LOW);
        
        switch(pressed)
        {
          case B_IN_ARM:
            digitalWrite(IN_ARM,HIGH);
       
          break;
          case B_IN_SAFETY:
            digitalWrite(IN_SAFETY,HIGH);
 
          break;
          case B_MCU_OUT_INT:
            digitalWrite(MCU_OUT_INT,HIGH);
            
          break;
          case B_INTERLOCK:
            digitalWrite(INTERLOCK,HIGH);
          
          break;
          case B_IN_MOD_DIR:
            digitalWrite(IN_MOD_DIR,HIGH);
          
          break;
          case B_GND:
            digitalWrite(GND,HIGH);
          
          break;
          default:
            digitalWrite(IN_ARM,LOW);
            digitalWrite(IN_SAFETY,LOW);
            digitalWrite(MCU_OUT_INT,LOW);
            digitalWrite(INTERLOCK,LOW);
            digitalWrite(IN_MOD_DIR,LOW);
            digitalWrite(GND,LOW);
          
          break;
       }
       active = pressed;
       Serial.print("Active: ");
       Serial.println(active);
      }
    }
    
    
  }
}
