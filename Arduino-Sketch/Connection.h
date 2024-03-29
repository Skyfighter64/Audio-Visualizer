#ifndef CONNECTION_H
#define CONNECTION_H
#include<Arduino.h>

class Connection
{
    public:
        /**
         * function establishing the connection
         */
        virtual void Connect() = 0;
        /**
         * function terminating the connection
         */
        virtual void Disconnect() = 0;
        /**
         * function sending the given bytes
         * @param bytes: a byte array containing the bytes to send
         * @param length: the length of the given array
         */
        virtual void Send(uint8_t* bytes, size_t length) = 0;
        /**
         * function receiving the given amount of bytes
         * Note: blocks until the given amount of bytes was read
         * @param buffer: a pre-initialized buffer of the given size to store the result
         * @param size: the size of the buffer
         * @return: the number of bytes read 
         */
        virtual int Read(uint8_t* buffer, size_t length) = 0;
         /**
         * function returning the number of bytes in the read buffer
         * @return: the number of bytes ready to read from the buffer
         */
        virtual int Available() = 0;
         /**
         * function returning if the connection is established
         * @return: true if connected, else false
         */
        virtual bool isConnected() = 0;
};


#endif