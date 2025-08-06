from machine import UART, Pin
import time
import constants
import hardware
import game_logic
from neopixel import Neopixel



def main():
    #First initialize everything
    uart, spi, cs, adc, game_leds, colon_leds, beam_a, beam_b, start, select, busy_pin = hardware.init_hardware()
    hardware.init_scoreboard(cs, spi)
    game_logic.turnOffLEDs(cs, spi, colon_leds)
    # Init game state
    game = game_logic.GameState()
    
    #init pixels
    pixels = Neopixel(constants.NUM_PIXELS, constants.STATE_MACHINE, constants.PIXEL_PIN, constants.COLOR_PATTERN)
    
    #turn on lights
    pixels.fill((255, 255, 255))
    pixels.show()
    
    #turn on first indicator
    game_leds[0].value(1)
    for i in range(6):
        game_leds[i+1].value(0)
    colon_leds[0].value(0)
    colon_leds[1].value(0)
    
    
    
    time.sleep(1.5)
    volume = (adc.read_u16() * 31) // 65535
    hardware.uart_write(uart, constants.SET_VOLUME, 0x00, volume)
    game.current_volume = volume
    hardware.uart_write(uart, constants.PLAY_SONG, 0, 1)
    while(busy_pin.value()):
        #get flags
        flags = {
        'f_start' : hardware.f_start,
        'f_select' : hardware.f_select,
        'f_goalA' : hardware.f_goalA,
        'f_goalB' : hardware.f_goalB
        }
        if(flags['f_start']):
            break
    time.sleep(0.1)
    hardware.uart_write(uart, constants.SET_FOLDER, constants.SELECT_SOUNDS, 0x01)
    
    while True:
        #get flags
        flags = {
        'f_start' : hardware.f_start,
        'f_select' : hardware.f_select,
        'f_goalA' : hardware.f_goalA,
        'f_goalB' : hardware.f_goalB
        }
        
        if game.state == 'SELECT':
            game_logic.handle_select(game, cs, spi, adc, uart, flags, game_leds, colon_leds, start, select, pixels, busy_pin)
        elif game.state == 'GAME_RUNNING':
            game_logic.handle_game_running(game, cs, spi, uart, flags, adc, colon_leds, pixels, busy_pin)
        elif game.state == 'GAME_END':
            game_logic.handle_game_end(game, cs, spi, uart, colon_leds, flags, pixels, busy_pin)
                    
        hardware.clear_flags()      # clear flags on each loop
        
        time.sleep_ms(10)  # loop timing
        
        
main()