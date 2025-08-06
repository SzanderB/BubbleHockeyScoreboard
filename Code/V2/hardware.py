from machine import Pin, SPI, I2C, ADC, Timer, UART
import time
import constants

f_start = False
f_select = False
f_goalA = False
f_goalB = False

#These are used to debounce the button and goal sensors
debounce_timer = Timer()


def spi_write(cs, spi, reg, data):
    cs.value(0)
    spi.write(bytearray([reg, data]))
    cs.value(1)
    
def uart_write(uart, cmd, param1=0, param2=1):
    msg = bytearray([
        0x7E, 0xFF, 0x06, cmd, 0x00,
        param1, param2,
        0x00, 0x00, 0xEF
    ])
    checksum = 0 - sum(msg[1:7]) & 0xFFFF
    msg[7] = (checksum >> 8) & 0xFF
    msg[8] = checksum & 0xFF
    uart.write(msg)
    

def init_UART():
    uart = UART(0, baudrate=9600, tx=Pin(constants.UART_TX), rx=Pin(constants.UART_RX))
    busy_pin = Pin(constants.BUSY_PIN, Pin.IN, Pin.PULL_UP)
    return uart, busy_pin
    
def init_SPI():
    sck= Pin(constants.SCLK_PIN)
    mosi = Pin(constants.MOSI_PIN)
    miso = Pin(constants.MISO_PIN)
    spi = SPI(1, baudrate = 400000, polarity = 0, phase = 0, firstbit=SPI.MSB, sck=sck, mosi=mosi, miso=miso)
    cs = Pin(constants.CS_PIN,mode = Pin.OUT, value = 1)
    return spi, cs
    
def init_ADC():
    adc = ADC(Pin(constants.ADC_PIN))
    return adc
    
def init_GameLEDs():
    gamemode_leds = [Pin(led, Pin.OUT) for led in constants.LED_GAMEMODE]
    return gamemode_leds
    
def init_TimeLEDs():
    colon_leds = [Pin(led, Pin.OUT) for led in constants.LED_COLON]
    return colon_leds
    
def init_BTNs():
    start  = Pin(constants.START_BTN, Pin.IN, Pin.PULL_UP)
    select = Pin(constants.SELECT_BTN, Pin.IN, Pin.PULL_UP)
    
    start.irq(trigger=Pin.IRQ_FALLING, handler=start_rst_handler)
    select.irq(trigger=Pin.IRQ_FALLING, handler=select_handler)
    return start, select
    
def init_beams():
    beam_a = Pin(constants.BEAM_A, Pin.IN, Pin.PULL_UP)   # Goal detection
    beam_b = Pin(constants.BEAM_B, Pin.IN, Pin.PULL_UP)
    
    beam_a.irq(trigger=Pin.IRQ_FALLING, handler=beam_a_handler)
    beam_b.irq(trigger=Pin.IRQ_FALLING, handler=beam_b_handler)
    return beam_a, beam_b
    

#collect all the objects i need in main and return in 1 package
def init_hardware():
    uart, busy_pin = init_UART()
    spi, cs = init_SPI()
    adc = init_ADC()
    game_leds = init_GameLEDs()
    colon_leds = init_TimeLEDs()
    beam_a, beam_b = init_beams()
    start, select = init_BTNs()
    
    return uart, spi, cs, adc, game_leds, colon_leds, beam_a, beam_b, start, select, busy_pin

def init_scoreboard(cs, spi):
    # Initialize MAX7219
    spi_write(cs, spi, constants.DISPLAY_TEST, 0x00)  # Display test off
    spi_write(cs, spi, constants.SHUTDOWN, 0x01)  # Shutdown register: normal operation
    spi_write(cs, spi, constants.DECODE_MODE, 0xFF)  # Decode mode: BCD for all digits
    spi_write(cs, spi, constants.INTENSITY, 0x0F)  # Intensity: max
    spi_write(cs, spi, constants.SCAN_LIMIT, 0x07)  # display all digits
    
    
#helpful things for hardware
def turnLEDsOff(cs, spi):
    spi_write(cs, spi, constants.SHUTDOWN, 0x0)
    
def turnLEDsOn(cs, spi):
    spi_write(cs, spi, constants.SHUTDOWN, 0x1)
    
    
    
#ISR Handlers
    #START BUTTON
def start_rst_handler(pin):
    debounce_timer.init(mode=Timer.ONE_SHOT, period=30, callback=lambda t: start_debounced(pin))
    
def start_debounced(pin):
    debounce_timer.deinit()
    if not pin.value():  # check that it's still pressed
        global f_start
        f_start = True
    
    #SELECT BUTTON
def select_handler(pin):
    debounce_timer.init(mode=Timer.ONE_SHOT, period=30, callback=lambda t: select_debounced(pin))
    
def select_debounced(pin):
    debounce_timer.deinit()
    if not pin.value():  # check that it's still pressed
        global f_select
        f_select = True
        
def beam_a_handler(pin):
    debounce_timer.init(mode=Timer.ONE_SHOT, period=10, callback=lambda t: beam_a_debounced(pin))

def beam_a_debounced(pin):
    debounce_timer.deinit()
    if not pin.value():
        global f_goalA
        f_goalA = True

def beam_b_handler(pin):
    debounce_timer.init(mode=Timer.ONE_SHOT, period=10, callback=lambda t: beam_b_debounced(pin))

def beam_b_debounced(pin):
    debounce_timer.deinit()
    if not pin.value():
        global f_goalB
        f_goalB = True
    
def clear_flags():
    global f_start, f_select, f_goalA, f_goalB
    f_start = False
    f_select = False
    f_goalA = False
    f_goalB = False