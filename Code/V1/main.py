# library imports…
import hardware
import game_logic
import time
import constants


#lcd_timer = Timer(3)
#lcd_timer.init(freq = 0.5, mode = Timer.PERIODIC, callback=lcd_update)

def main():
# Init hardware
    player_a_leds, player_b_leds = hardware.init_LEDs()
    start, beam_a, beam_b = hardware.init_sensors()
    spi, cs = hardware.init_DAC()
    lcd = hardware.init_LCD()
    adc = hardware.init_adc()

    # Init game state
    game = game_logic.GameState()


    lcd_update_time = time.ticks_ms()
    lcd_update = {'update' : True}
    while True:
        #get flags
        flags ={
        'f_start' : hardware.button_pressed,
        'f_goal_a' : hardware.goal_a_flag,
        'f_goal_b' : hardware.goal_b_flag
        }
        
        
        if(time.ticks_ms()-lcd_update_time > 500):
            lcd_update['update'] = True
            lcd_update_time = time.ticks_ms()

        if game.state == 'SELECT':
            game_logic.handle_select(game, adc, flags, lcd, lcd_update)
        elif game.state == 'GAME_RUNNING':
            game_logic.handle_game_running(game, player_a_leds, player_b_leds, flags, lcd, lcd_update)

        elif game.state == 'SCORE_SCREEN':
            game_logic.handle_score_screen(game, cs, spi, lcd, lcd_update)

        elif game.state == 'GAME_END':
            game_logic.handle_game_end(game, cs, spi, lcd, lcd_update, player_a_leds, player_b_leds)
            # make a new game
            game = game_logic.GameState()
        
        hardware.clear_flags()      # clear flags on each loop
        
        time.sleep_ms(10)  # loop timing

main()


# gonna have LCD update every 0.5 second to save time