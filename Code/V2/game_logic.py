# game_logic.py is like the datapath and handles all the logic for each state
import time
from machine import Pin, SPI, I2C, ADC, Timer
import constants
import hardware
from neopixel import Neopixel


GAME_OPTIONS = [
    {'mode': 'SCORE', 'target_score': 3},
    {'mode': 'SCORE', 'target_score': 5},
    {'mode': 'SCORE', 'target_score': 7},
    {'mode': 'TIMER', 'target_time': 180},
    {'mode': 'TIMER', 'target_time': 300},
    {'mode': 'TIMER', 'target_time': 420},
    {'mode': 'FREEPLAY', 'target_time': 0}
]

class GameState:
    def __init__(self):
        self.state = 'SELECT'
        self.mode_num = 0
        self.mode = 'SCORE'         # or timer
        self.target_score = 3
        self.score_a = 0
        self.score_b = 0
        self.target_time = 300      # in seconds, so 5 mins
        self.update_time = time.ticks_ms()
        self.start_time = time.ticks_ms()
        self.current_volume = 30
        self.red_state = False
        

def handle_select(game, cs, spi, adc, uart, flags, game_leds, colon_leds, start, select, pixels, busy_pin):
    # read potentiometer for char and map to 0-30 for volume
    volume = (adc.read_u16() * 31) // 65535
    if volume != game.current_volume:
        hardware.uart_write(uart, constants.SET_VOLUME, 0x00, volume)
        game.current_volume = volume
    
    if(flags['f_start']):
        game.state='GAME_RUNNING'
        game.start_time = time.ticks_ms()
        #turn on display
        setScore(cs, spi, 'A', 0)
        setScore(cs, spi, 'B', 0)
        for i in range(2):
            colon_leds[i].value(1)
        flags['f_start'] = False
            
    if(flags['f_select']):
        pixels.fill((255, 255, 255))
        pixels.show()
        game.mode_num = (game.mode_num + 1)%(len(GAME_OPTIONS))
        game.mode = GAME_OPTIONS[game.mode_num]['mode']
        if(game.mode_num < 3):
            game.target_score = GAME_OPTIONS[game.mode_num]['target_score']
        else:
            game.target_time = GAME_OPTIONS[game.mode_num]['target_time']
        for i in range(len(GAME_OPTIONS)):
            if(i == game.mode_num):
                game_leds[i].value(1)
            else:
                game_leds[i].value(0)
        hardware.uart_write(uart, constants.SET_FOLDER, constants.SELECT_SOUNDS, game.mode_num + 1)
        flags['f_select'] = False
    pass

def handle_game_running(game, cs, spi, uart, flags, adc, colon_leds, pixels, busy_pin):
    # read potentiometer for char and map to 0-3 for volume
    volume = (adc.read_u16() * 31) // 65535
    if volume != game.current_volume:
        hardware.uart_write(uart, constants.SET_VOLUME, 0x00, volume)
        game.current_volume = volume
        
    print(busy_pin.value())
    if(flags['f_start']):
        game.state = 'SELECT'
        turnOffLEDs(cs, spi, colon_leds)
        game.score_a = 0
        game.score_b = 0
        return
    
    if(flags['f_goalA']):
        game.score_a += 1
        #Send to max to update
        setScore(cs, spi, 'A', game.score_a)
        if game.mode == 'SCORE' and game.score_a >= game.target_score:
            hardware.uart_write(uart, constants.SET_FOLDER, constants.GAME_SOUNDS, constants.END_GOAL)
        else:
            hardware.uart_write(uart, constants.SET_FOLDER, constants.GAME_SOUNDS, constants.HORN)
        pixels.fill((255, 0, 0))
        pixels.show()
        game.red_state = True
        time.sleep(0.1)
        
    if(flags['f_goalB']):
        game.score_b += 1
        setScore(cs, spi, 'B', game.score_b)
        if game.mode == 'SCORE' and game.score_b >= game.target_score:
            hardware.uart_write(uart, constants.SET_FOLDER, constants.GAME_SOUNDS, constants.END_GOAL)
        else:
            hardware.uart_write(uart, constants.SET_FOLDER, constants.GAME_SOUNDS, constants.HORN)
        pixels.fill((255, 0, 0))
        pixels.show()
        game.red_state = True
        time.sleep(0.1)
        
    #turn off red LED if needed
    if game.red_state and busy_pin.value():
        pixels.fill((255, 255, 255))
        pixels.show()
        game.red_state = False
    
    if (time.ticks_diff(time.ticks_ms(), game.update_time) > 200):
        minutes, seconds = get_game_time(game)
        setClock(cs, spi, minutes, seconds)
        game.update_time = time.ticks_ms()
    
    # if timer or score limit: change to 'GAME_END'
    if game.mode == 'SCORE':
        if game.score_a >= game.target_score or game.score_b >= game.target_score:
            game.state = 'GAME_END'
            time.sleep(0.1)
            while not busy_pin.value():
                continue
            time.sleep(0.1)
            if game.score_a > game.score_b:
                hardware.uart_write(uart, constants.SET_FOLDER, constants.END_SOUNDS, constants.RED_WIN)
            elif game.score_a < game.score_b:
                hardware.uart_write(uart, constants.SET_FOLDER, constants.END_SOUNDS, constants.BLACK_WIN)
            else:
                hardware.uart_write(uart, constants.SET_FOLDER, constants.END_SOUNDS, constants.TIE)

    elif game.mode == 'TIMER':
        elapsed = time.ticks_diff(time.ticks_ms(), game.start_time) // 1000
        if elapsed >= game.target_time:
            hardware.uart_write(uart, constants.SET_FOLDER, constants.END_SOUNDS, constants.FINAL_TIME)
            setClock(cs, spi, 0, 0)
            game.state = 'GAME_END'
                #check if audio is busy
            time.sleep(0.1)
            while not busy_pin.value():
                continue
            time.sleep(0.1)
            if game.score_a > game.score_b:
                hardware.uart_write(uart, constants.SET_FOLDER, constants.END_SOUNDS, constants.RED_WIN)
            elif game.score_a < game.score_b:
                hardware.uart_write(uart, constants.SET_FOLDER, constants.END_SOUNDS, constants.BLACK_WIN)
            else:
                hardware.uart_write(uart, constants.SET_FOLDER, constants.END_SOUNDS, constants.TIE)

    pass


def handle_game_end(game, cs, spi, uart, colon_leds, flags, pixels, busy_pin):
    
    if(flags['f_start']):
        game.state = 'SELECT'
        turnOffLEDs(cs, spi, colon_leds)
        pixels.fill((255, 255, 255))
        pixels.show()
        game.red_state = False
        
        game.score_a = 0
        game.score_b = 0
        hardware.uart_write(uart, constants.SET_FOLDER, constants.SELECT_SOUNDS, game.mode_num + 1)

    pass

def get_game_time(game):
    elapsed = time.ticks_diff(time.ticks_ms(), game.start_time) // 1000  # in seconds

    if game.mode == 'TIMER':
        remaining = max(0, game.target_time - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        return minutes, seconds
    else:
        # Just show elapsed time in SCORE mode
        minutes = elapsed // 60
        seconds = elapsed % 60
        return minutes, seconds

def setScore(cs, spi, team, score):
    if(team == 'A'):
        hardware.spi_write(cs, spi, constants.DIG0, (int)(score/10))
        hardware.spi_write(cs, spi, constants.DIG1, (score%10))
    else:
        hardware.spi_write(cs, spi, constants.DIG6, (int)(score/10))
        hardware.spi_write(cs, spi, constants.DIG7, (score%10))
        
def setClock(cs, spi, minutes, seconds):
    hardware.spi_write(cs, spi, constants.DIG2, (int)(minutes/10))
    hardware.spi_write(cs, spi, constants.DIG3, minutes%10)
    hardware.spi_write(cs, spi, constants.DIG4, (int)(seconds/10))
    hardware.spi_write(cs, spi, constants.DIG5, seconds%10)
    
def turnOffLEDs(cs, spi, colon_leds):
    hardware.spi_write(cs, spi, constants.DIG0, 0x0F)
    hardware.spi_write(cs, spi, constants.DIG1, 0x0F)
    hardware.spi_write(cs, spi, constants.DIG2, 0x0F)
    hardware.spi_write(cs, spi, constants.DIG3, 0x0F)
    hardware.spi_write(cs, spi, constants.DIG4, 0x0F)
    hardware.spi_write(cs, spi, constants.DIG5, 0x0F)
    hardware.spi_write(cs, spi, constants.DIG6, 0x0F)
    hardware.spi_write(cs, spi, constants.DIG7, 0x0F)
    for i in range(2):
        colon_leds[i].value(0)

    
