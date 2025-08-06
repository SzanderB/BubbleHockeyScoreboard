from machine import Pin, SPI
pinSCK = 14
pinCS  = 13
pinTX  = 15

def main():
    #set up SPI to DAC
    sck= Pin(pinSCK)
    mosi = Pin(pinTX)
    spi = SPI(1, baudrate = 400000, polarity = 0, phase = 0, firstbit=SPI.MSB, sck=sck, mosi=mosi, miso=None)
    cs = Pin(pinCS,mode = Pin.OUT, value = 1)

    #write to decode
    cs.value(0)
    buf=bytearray([0x09, 0xFF])
    spi.write(buf)
    cs.value(1)

    #write to intensity
    cs.value(0)
    buf=bytearray([0x0A, 0x0F])
    spi.write(buf)
    cs.value(1)
    
    #write to scan limit
    cs.value(0)
    buf=bytearray([0x0B, 0x01])
    spi.write(buf)
    cs.value(1)
    
    #write to digit 0
    cs.value(0)
    buf=bytearray([0x01, 0x01])
    spi.write(buf)
    cs.value(1)
    
    #write to digit 1
    cs.value(0)
    buf=bytearray([0x02, 0x02])
    spi.write(buf)
    cs.value(1)
    
    print("Done")
main()