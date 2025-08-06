from machine import Pin, SPI, I2C, ADC, Timer
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
import constants

# These will be updated by the ISR
button_pressed = False
goal_a_flag = False
goal_b_flag = False

button_timer = Timer()
goal_timer = Timer()

def init_LCD():
    #initialize your i2c module and lcd
    i2c = I2C(0, sda=Pin(constants.SDA_pin), scl=Pin(constants.SCL_pin), freq=400000)
    lcd = I2cLcd(i2c, constants.I2C_ADDR, constants.I2C_NUM_ROWS, constants.I2C_NUM_COLS)
    return lcd


def init_DAC():
    
    #set up SPI to DAC
    sck= Pin(constants.pinSCK)
    mosi = Pin(constants.pinTX)
    spi = SPI(1, baudrate = 1000000, polarity = 0, phase = 0, firstbit=SPI.MSB, sck=sck, mosi=mosi, miso=None)
    cs = Pin(constants.pinCS,mode = Pin.OUT, value = 1)
    return spi, cs

def init_adc():
    adc = ADC(Pin(constants.pinADC))
    return adc


def init_sensors():
    # Buttons & goal sensor
    start_button = Pin(constants.pinButton, Pin.IN, Pin.PULL_UP)  # Start game
    beam_a = Pin(constants.pinSensorA, Pin.IN, Pin.PULL_UP)   # Goal detection
    beam_b = Pin(constants.pinSensorB, Pin.IN, Pin.PULL_UP)
    
    start_button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)
    beam_a.irq(trigger=Pin.IRQ_FALLING, handler=beam_a_handler)
    beam_b.irq(trigger=Pin.IRQ_FALLING, handler=beam_b_handler)
    return start_button, beam_a, beam_b

def init_LEDs():
    # 2 arrays of 5 leds each from constants.py

    # simple for loop to get all pins
    player_a_leds = [Pin(pin, Pin.OUT) for pin in constants.player_a_pins]
    player_b_leds = [Pin(pin, Pin.OUT) for pin in constants.player_b_pins]

    return player_a_leds, player_b_leds



# ISRs that update globals to use in other files
def button_handler(pin):
    button_timer.init(mode=Timer.ONE_SHOT, period=50, callback=button_debounced)

    
def button_debounced(t):
    global button_pressed
    button_pressed = True
    button_timer.deinit()

    
def beam_a_handler(pin):
    goal_timer.init(mode=Timer.ONE_SHOT, period=2, callback=beam_a_debounced)

def beam_a_debounced(t):
    goal_timer.deinit()
    global goal_a_flag
    goal_a_flag = True

def beam_b_handler(pin):
    goal_timer.init(mode=Timer.ONE_SHOT, period=2, callback=beam_b_debounced)

def beam_b_debounced(t):
    goal_timer.deinit()
    global goal_b_flag
    goal_b_flag = True

def clear_flags():
    global button_pressed, goal_a_flag, goal_b_flag
    button_pressed = False
    goal_a_flag = False
    goal_b_flag = False
