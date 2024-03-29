#ifndef CONVERT_H
#define CONVERT_H

#include <Arduino.h>

class Convert
{
    public: 
        /**
         * function converting the given text to UTF-8 bytes including a null terminator
         * @param text: the text to convert
         * @param outBytes: the converted text including a null terminator; has to have a size of text.length() + 1
         * @param outBytesLength: the length of the outBytes array; has to be text.length() + 1
         */
        static void StringToBytes(String text, byte* outBytes, int outBytesLength)
        {
            text.getBytes(outBytes, outBytesLength);
        }

        /**
         * function converting a 32bit integer to an array of 4 bytes
         * @param number: the number which should be converted
         * @param outBytes: a pointer to the byte array where the result will be stored; has to have a size of 4
         * @return: an integer representing the length of the outBytes array
         */
        static int Int32ToBytes(long number, byte * outBytes)
        {
            outBytes[0] = (number >> 24) & 0xFF;
            outBytes[1] = (number >> 16) & 0xFF;
            outBytes[2] = (number >> 8) & 0xFF;
            outBytes[3] = number & 0xFF;
            
            return 4;
        }

        /**
        *function converting 4 bytes to a 32 bit integer
        *@param bytes: an array of 4 bytes which should be converted
        *@return: the integer converted from the given bytes
        */
        static int32_t BytesToInt32(byte bytes[])
        {
            int32_t number = 0;

            //shift each byte to its correspondig position and add it to the number
            number += (int32_t) bytes[0] << 24;
            number += (int32_t) bytes[1] << 16;
            number += (int32_t) bytes[2] << 8;
            number += (int32_t) bytes[3];
            
            return number;
        }


};

#endif