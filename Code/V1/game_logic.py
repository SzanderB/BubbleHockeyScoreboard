# game_logic.py is like the datapath and handles all the logic for each state
import time
from machine import Pin, SPI, I2C, ADC, Timer
import constants


GAME_OPTIONS = [
    {'mode': 'SCORE', 'target_score': 3},
    {'mode': 'SCORE', 'target_score': 5},
    {'mode': 'TIMER', 'target_time': 180},
    {'mode': 'TIMER', 'target_time': 300},
    {'mode': 'TIMER', 'target_time': 420},
]

sine_timer = Timer()
table_index = 0

class GameState:
    def __init__(self):
        self.state = 'SELECT'
        self.mode = 'SCORE'         # or timer
        self.target_score = 5
        self.score_a = 0
        self.score_b = 0
        self.target_time = 300      # in seconds, so 5 mins
        self.goal_time = 0
        self.start_time = time.ticks_ms()

def handle_select(game, adc, flags, lcd, lcd_update):

    
    # read potentiometer for char and map to 0-4 for state select
    val = (adc.read_u16() * len(GAME_OPTIONS)) // constants.MAXU16

    selected = GAME_OPTIONS[val]
    game.mode = selected['mode']
    game.target_score = selected.get('target_score', 0)     # gets target score if there is one
    game.target_time = selected.get('target_time', 0)       # same here
    # wait for button press → move to 'GAME_RUNNING'
    
        #update lcd if needed
    
    if(lcd_update['update']):
        lcd_update['update'] = False
        lcd.clear()
        lcd.putstr("Gamemode: ")
        lcd.move_to(0,1)
        if game.target_score != 0:
            lcd.putstr(f"{game.mode} to {game.target_score}")
        else:
            lcd.putstr(f"{game.mode} for {game.target_time}s")
    if(flags['f_start']):
        game.state='GAME_RUNNING'
        lcd_update['update'] = True
        game.start_time = time.ticks_ms()
    pass

def handle_game_running(game, leds_a, leds_b, flags, lcd, lcd_update):
    # update lcd if needed
    if(lcd_update['update']):
        lcd_update['update'] = False
        lcd.clear()
        #place time
        lcd.move_to(0, 0)
        lcd.putstr("A  TIME: " + get_game_time(game) + "  B")
        #place scores
        lcd.move_to(0, 1)
        lcd.putstr("{}".format(game.score_a))
        lcd.move_to(15, 1)
        lcd.putstr("{}".format(game.score_b))

    # check beam break → update score
    if(flags['f_start']):
        game.state = "SELECT"
        game.score_a = 0
        game.score_b = 0
        lcd_update['update'] = True
    # if goal: change to 'SCORE_SCREEN'
    if(flags['f_goal_a']):
        game.score_a += 1
        game.state = "SCORE_SCREEN"
    if(flags['f_goal_b']):
        game.score_b += 1
        game.state = "SCORE_SCREEN"
    # update LED arrays
    if(game.mode == 'SCORE'):
        for i in range(game.score_a):
            leds_a[i].value(1)
        for i in range(game.score_b):
            leds_b[i].value(1)
    
    # if timer or score limit: change to 'GAME_END'
    if game.mode == 'SCORE':
        if game.score_a >= game.target_score or game.score_b >= game.target_score:
            game.state = 'GAME_END'

    elif game.mode == 'TIMER':
        elapsed = time.ticks_diff(time.ticks_ms(), game.start_time) // 1000
        if elapsed >= game.target_time:
            game.state = 'GAME_END'
    pass

def handle_score_screen(game, cs, spi, lcd, lcd_update):
    # wait 3 seconds → return to 'GAME_RUNNING'
    #set LCD to Score!
    lcd.clear()
    lcd.putstr(f"GOOOOOOOOOOOOAL!")

    # start sine_timer
    start_sine_wave(cs, spi)
    #sit in while loop
    start = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start) < 3000:
        time.sleep_ms(1)
    stop_sine_wave()
    game.state = 'GAME_RUNNING'
    lcd_update['update'] = True
    pass

def handle_game_end(game, cs, spi, lcd, lcd_update, leds_a, leds_b):
    # wait 5 seconds → reset game → 'SELECT'
    # set LCD to winner of game
    lcd.clear()
    if(game.mode == 'TIMER' and game.score_a == game.score_b):
        lcd.putstr(f"Tie!")
    elif(game.score_a > game.score_b):
        lcd.putstr(f"Team Red Wins!")
    else:
        lcd.putstr(f"Team Black Wins!")
    # start sine_timer
    start_sine_wave(cs, spi)
    #sit in while loop
    start = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start) < 5000:
        time.sleep_ms(1)

    stop_sine_wave()
    for i in range(5):
        leds_a[i].value(0)
    for i in range(5):
        leds_b[i].value(0)

    game.state = 'SELECT' # redundant since itll be reset in main but here anyways
    lcd_update['update'] = True
    pass


def get_game_time(game):
    elapsed = time.ticks_diff(time.ticks_ms(), game.start_time) // 1000  # in seconds

    if game.mode == 'TIMER':
        remaining = max(0, game.target_time - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes:01}:{seconds:02}"  # e.g. "2:03"
    else:
        # Just show elapsed time in SCORE mode
        minutes = elapsed // 60
        seconds = elapsed % 60
        return f"{minutes:01}:{seconds:02}"
    



# FOR TIMER STUFF
# SPI Send Function
def send_to_dac(value, cs, spi):
    global table_index
    cs.value(0)
    buf=bytearray([constants.loadwakeA | (value >> 6), (value<<2) & 0xFC])
    spi.write(buf)
    cs.value(1)

# Timer Interrupt to Send Sine Wave
def sine_wave_callback(cs, spi):
    global table_index
    send_to_dac(constants.sineLUT[table_index], cs, spi)
    table_index = (table_index + 1) % len(constants.sineLUT)  # Loop through sine wave table

# Timer to generate 350 Hz sine wave
def start_sine_wave(cs, spi):
    sine_timer.init(freq=constants.freq_out*len(constants.sineLUT), mode=Timer.PERIODIC, callback=lambda t: sine_wave_callback(cs, spi))

# Stop the sine wave
def stop_sine_wave():
    sine_timer.deinit()

