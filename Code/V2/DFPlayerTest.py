from machine import UART, Pin
import time

uart = UART(0, baudrate=9600, tx=Pin(12), rx=Pin(13))

def send_cmd(cmd, param1=0, param2=1):
    msg = bytearray([
        0x7E, 0xFF, 0x06, cmd, 0x00,
        param1, param2,
        0x00, 0x00, 0xEF
    ])
    checksum = 0 - sum(msg[1:7]) & 0xFFFF
    msg[7] = (checksum >> 8) & 0xFF
    msg[8] = checksum & 0xFF
    uart.write(msg)

time.sleep(2)      # Allow DFPlayer to initialize
send_cmd(0x03, 0x00, 0x01)  # Play track 1
time.sleep(5)      # Wait before switching
send_cmd(0x03, 0x00, 0x02)  # Play track 2
