#ifndef FRAME_H
#define FRAME_H

#include <Arduino.h>
/**
 * class representing a frame as defined in the ALUP v.0.2
 */
class Frame
{
    public:
      //array containing the data of this frame
      byte* body;
      //the size of the data
      int32_t body_size;
      //the offset of the first body value
      int32_t offset;
      //the command byte
      uint8_t command;
      //leftover byte, reserved for future use
      uint8_t unused;
        
};
enum Command
{
  NONE = 0,
  CLEAR = 1,
  DISCONNECT = 2,
  TOGGLE_INTERNAL_LED = 4
};

#endif