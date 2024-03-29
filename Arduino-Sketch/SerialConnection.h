#ifndef SERIAL_CONNECTION_H
#define SERIAL_CONNECTION_H

#include "Connection.h"
#include "Arduino.h"

#define SERIAL_TIMEOUT_MS 10000

/**
 * class implementing serial connectivity for this library
 */

class SerialConnection : public Connection
{
public:
    /**
     * default constructor
     * @param _baud: the communication speed of the devices
     */
    SerialConnection(long _baud) : baud{_baud}
    {
      
    }

    long baud = 115200;

    /**
     * function establishing the connection
     */
    void Connect()
    {
        //set the serial timeout to 10s
        //this value may need adjustment
        Serial.setTimeout(SERIAL_TIMEOUT_MS);
        Serial.begin(baud);    
        delay(100);   
    }
    /**
     * function terminating the connection
     */
    void Disconnect()
    {
        Serial.end();
    }
    /**
     * function sending the given bytes
     * @param bytes: a byte array containing the bytes to send
     * @param length: the length of the given array
     */
    void Send(uint8_t* bytes, size_t length)
    {
        Serial.write(bytes, length);
    }
    /**
     * function receiving the given amount of bytes
     * Note: blocks until the given amount of bytes was read
     * @param buffer: a pre-initialized buffer of the given size
     * @param size: the size of the buffer
     * @return: the number of bytes read 
     */
    int Read(uint8_t* buffer, size_t length) 
    {
        while(Available() < length)
        {
          //wait for data
        } 
        
        return Serial.readBytes(buffer, length);
    }
    /**
     * function returning the number of bytes in the read buffer
     * @return: the number of bytes ready to read from the buffer
     */
    int Available()
    {
        return Serial.available();
    }
    /**
     * function returning if the connection is established
     * @return: true if connected, else false
     */
    virtual bool isConnected()
    {
        return Serial;
    }
};

#endif
