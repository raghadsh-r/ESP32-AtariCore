from machine import Pin, ADC, I2C, PWM
import ssd1306
import time
import random

# ================== OLED ==================
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# ================== JOYSTICK ==================
joy_x = ADC(Pin(34))
joy_y = ADC(Pin(35))
joy_x.atten(ADC.ATTN_11DB)
joy_y.atten(ADC.ATTN_11DB)

joy_sw = Pin(32, Pin.IN, Pin.PULL_UP)

# ================== BUTTONS ==================
btn_a = Pin(25, Pin.IN, Pin.PULL_UP)      # Select / Shoot / Jump
btn_up = Pin(26, Pin.IN, Pin.PULL_UP)     # Up
btn_down = Pin(27, Pin.IN, Pin.PULL_UP)   # Down
btn_back = Pin(14, Pin.IN, Pin.PULL_UP)   # Back to menu

# ================== LEDS ==================
led_green = Pin(2, Pin.OUT)    # Ready / Power
led_blue = Pin(4, Pin.OUT)     # Menu
led_yellow = Pin(5, Pin.OUT)   # Score
led_red = Pin(19, Pin.OUT)     # Game Over

# ================== BUZZER ==================
buzzer = PWM(Pin(18))
buzzer.duty(0)

# ================== GAMES ==================
games = [
    {"name": "SNAKE", "icon": "oooo", "desc": "Eat & grow"},
    {"name": "PONG", "icon": "| o |", "desc": "Bounce ball"},
    {"name": "CATCH", "icon": "\\_/", "desc": "Catch items"},
    {"name": "FLAPPY", "icon": "<o>", "desc": "Avoid pipes"},
    {"name": "INVADERS", "icon": "/A\\", "desc": "Shoot enemy"},
]

menu_index = 0
last_move = time.ticks_ms()

# ================== LED HELPERS ==================
def leds_off():
    led_green.value(0)
    led_blue.value(0)
    led_yellow.value(0)
    led_red.value(0)

def led_ready():
    leds_off()
    led_green.value(1)

def led_menu():
    leds_off()
    led_blue.value(1)

def led_playing():
    leds_off()
    led_green.value(1)

def led_score():
    led_yellow.value(1)
    time.sleep(0.04)
    led_yellow.value(0)

def led_game_over():
    leds_off()
    led_red.value(1)

# ================== CALIBRATION ==================
def read_avg(adc, n=25):
    total = 0
    for _ in range(n):
        total += adc.read()
        time.sleep(0.004)
    return total // n

def center_text(text, y, color=1):
    x = (128 - len(text) * 8) // 2
    oled.text(text, max(0, x), y, color)

led_ready()

oled.fill(0)
oled.rect(0, 0, 128, 64, 1)
center_text("MINI ATARI", 14)
center_text("Calibrating", 32)
center_text("Dont touch joy", 48)
oled.show()

CENTER_X = read_avg(joy_x)
CENTER_Y = read_avg(joy_y)
DEADZONE = 320

BASE_SW = joy_sw.value()
BASE_A = btn_a.value()
BASE_UP = btn_up.value()
BASE_DOWN = btn_down.value()
BASE_BACK = btn_back.value()

# ================== HELPERS ==================
def beep(freq=1000, duration=0.04):
    try:
        buzzer.freq(freq)
        buzzer.duty(250)
        time.sleep(duration)
        buzzer.duty(0)
    except:
        pass

def is_pressed(pin, base=1):
    return base == 1 and pin.value() == 0

def sw_pressed():
    return is_pressed(joy_sw, BASE_SW)

def a_pressed():
    return is_pressed(btn_a, BASE_A)

def up_button_pressed():
    return is_pressed(btn_up, BASE_UP)

def down_button_pressed():
    return is_pressed(btn_down, BASE_DOWN)

def back_pressed():
    return is_pressed(btn_back, BASE_BACK)
#X=UP/DOWN  ,Y= LEFT/RIGHT

def joy_up():
    return joy_x.read() < CENTER_X - DEADZONE

def joy_down():
    return joy_x.read() > CENTER_X + DEADZONE

def joy_left():
    return joy_y.read() < CENTER_Y - DEADZONE

def joy_right():
    return joy_y.read() > CENTER_Y + DEADZONE

def select_pressed():
    return joy_right() or sw_pressed() or a_pressed()

def exit_pressed():
    return back_pressed()

def menu_up_pressed():
    return joy_up() or up_button_pressed()

def menu_down_pressed():
    return joy_down() or down_button_pressed()

def wait_release():
    time.sleep(0.18)
    while (
        joy_right() or joy_up() or joy_down()
        or sw_pressed() or a_pressed()
        or up_button_pressed() or down_button_pressed()
        or back_pressed()
    ):
        time.sleep(0.02)

def draw_frame():
    oled.rect(0, 0, 128, 64, 1)
    oled.pixel(3, 3, 1)
    oled.pixel(124, 3, 1)
    oled.pixel(3, 60, 1)
    oled.pixel(124, 60, 1)

def splash():
    led_ready()

    oled.fill(0)
    draw_frame()
    center_text("RAGHAD & Reema", 7)
    center_text("MINI ATARI", 22)
    oled.hline(24, 35, 80, 1)
    center_text("ESP32 CONSOLE", 43)
    oled.show()

    beep(800, 0.04)
    time.sleep(0.12)
    beep(1200, 0.04)
    time.sleep(0.9)

def game_over(score):
    led_game_over()
    beep(250, 0.22)

    oled.fill(0)
    draw_frame()
    center_text("GAME OVER", 10)
    oled.hline(25, 24, 78, 1)
    center_text("SCORE: " + str(score), 32)
    center_text("A = MENU", 48)
    oled.show()

    while not select_pressed() and not exit_pressed():
        time.sleep(0.02)

    wait_release()
    led_menu()

# ================== MENU UI ==================
def draw_menu():
    led_menu()

    oled.fill(0)
    draw_frame()

    oled.fill_rect(0, 0, 128, 12, 1)
    oled.text(" MINI ATARI", 18, 2, 0)

    current = games[menu_index]

    oled.rect(8, 16, 112, 35, 1)
    oled.fill_rect(10, 18, 108, 10, 1)
    center_text(current["name"], 19, 0)

    center_text(current["icon"], 32)
    center_text(current["desc"], 43)

    if menu_index > 0:
        oled.text("^", 61, 13)

    if menu_index < len(games) - 1:
        oled.text("v", 61, 52)

    oled.text(str(menu_index + 1) + "/" + str(len(games)), 101, 2, 0)

    oled.text("UP/DN", 2, 56)
    oled.text("A/RIGHT", 68, 56)

    oled.show()

# ================== SNAKE ==================
def snake_game():
    led_playing()

    cell = 4
    snake = [(32, 32), (28, 32), (24, 32)]
    direction = 1
    food = (random.randrange(0, 32) * cell, random.randrange(0, 16) * cell)
    score = 0
    speed = 0.13

    while True:
        if exit_pressed():
            wait_release()
            led_menu()
            return

        if (joy_up() or up_button_pressed()) and direction != 2:
            direction = 0
        elif joy_right() and direction != 3:
            direction = 1
        elif (joy_down() or down_button_pressed()) and direction != 0:
            direction = 2
        elif joy_left() and direction != 1:
            direction = 3

        hx, hy = snake[0]

        if direction == 0:
            hy -= cell
        elif direction == 1:
            hx += cell
        elif direction == 2:
            hy += cell
        elif direction == 3:
            hx -= cell

        new_head = (hx, hy)

        if hx < 0 or hx >= 128 or hy < 0 or hy >= 64 or new_head in snake:
            game_over(score)
            return

        snake.insert(0, new_head)

        if abs(hx - food[0]) < cell and abs(hy - food[1]) < cell:
            score += 1
            beep(1500, 0.025)
            led_score()
            food = (random.randrange(0, 32) * cell, random.randrange(0, 16) * cell)

            if speed > 0.075:
                speed -= 0.004
        else:
            snake.pop()

        oled.fill(0)
        oled.text(str(score), 0, 0)
        oled.fill_rect(food[0], food[1], cell, cell, 1)

        for sx, sy in snake:
            oled.fill_rect(sx, sy, cell, cell, 1)

        oled.show()
        time.sleep(speed)

# ================== PONG ==================
def pong_game():
    led_playing()

    paddle_x = 54
    ai_x = 54
    ball_x = 64
    ball_y = 32
    ball_vx = 1
    ball_vy = 2
    score = 0

    while True:
        if exit_pressed():
            wait_release()
            led_menu()
            return

        if joy_left():
            paddle_x -= 3
        elif joy_right():
            paddle_x += 3

        paddle_x = max(0, min(108, paddle_x))

        if ball_x > ai_x + 10:
            ai_x += 2
        elif ball_x < ai_x + 10:
            ai_x -= 2

        ai_x = max(0, min(108, ai_x))

        ball_x += ball_vx
        ball_y += ball_vy

        if ball_x <= 0 or ball_x >= 126:
            ball_vx *= -1
            beep(700, 0.012)

        if ball_y >= 55 and paddle_x <= ball_x <= paddle_x + 20:
            ball_vy *= -1
            score += 1
            beep(1200, 0.018)
            led_score()

        if ball_y <= 6 and ai_x <= ball_x <= ai_x + 20:
            ball_vy *= -1

        if ball_y > 64:
            game_over(score)
            return

        if ball_y < 0:
            ball_vy *= -1

        oled.fill(0)
        oled.text(str(score), 0, 0)
        oled.fill_rect(ai_x, 2, 20, 4, 1)
        oled.fill_rect(paddle_x, 58, 20, 4, 1)
        oled.fill_rect(ball_x, ball_y, 3, 3, 1)
        oled.show()

        time.sleep(0.035)

# ================== CATCH ==================
def catch_game():
    led_playing()

    player_x = 55
    item_x = random.randint(0, 120)
    item_y = 0
    score = 0
    fall_speed = 2

    while True:
        if exit_pressed():
            wait_release()
            led_menu()
            return

        if joy_left():
            player_x -= 3
        elif joy_right():
            player_x += 3

        player_x = max(0, min(108, player_x))

        item_y += fall_speed

        if item_y >= 55:
            if player_x <= item_x <= player_x + 20:
                score += 1
                beep(1500, 0.02)
                led_score()

                item_x = random.randint(0, 120)
                item_y = 0

                if score % 5 == 0 and fall_speed < 5:
                    fall_speed += 1
            else:
                game_over(score)
                return

        oled.fill(0)
        oled.text("Score:" + str(score), 0, 0)
        oled.fill_rect(player_x, 58, 20, 4, 1)
        oled.fill_rect(item_x, item_y, 4, 4, 1)
        oled.show()

        time.sleep(0.045)

# ================== FLAPPY ==================
def flappy_game():
    led_playing()

    bird_y = 32
    velocity = 0
    pipe_x = 128
    pipe_gap = 25
    pipe_height = random.randint(8, 30)
    score = 0

    while True:
        if exit_pressed():
            wait_release()
            led_menu()
            return

        if select_pressed() or joy_up() or up_button_pressed():
            velocity = -2.9
            beep(1000, 0.012)
            time.sleep(0.035)

        velocity += 0.35
        bird_y += int(velocity)

        pipe_x -= 3

        if pipe_x < -12:
            pipe_x = 128
            pipe_height = random.randint(8, 30)
            score += 1
            beep(1400, 0.015)
            led_score()

        if bird_y < 0 or bird_y > 60:
            game_over(score)
            return

        if 15 <= pipe_x <= 24:
            if bird_y < pipe_height or bird_y > pipe_height + pipe_gap:
                game_over(score)
                return

        oled.fill(0)
        oled.text(str(score), 0, 0)

        oled.fill_rect(15, bird_y, 6, 5, 1)
        oled.pixel(21, bird_y + 2, 1)

        oled.fill_rect(pipe_x, 0, 10, pipe_height, 1)
        oled.fill_rect(pipe_x, pipe_height + pipe_gap, 10, 64 - (pipe_height + pipe_gap), 1)

        oled.show()
        time.sleep(0.04)

# ================== INVADERS ==================
def invaders_game():
    led_playing()

    player_x = 60
    bullet_x = -1
    bullet_y = -1
    enemy_x = random.randint(0, 110)
    enemy_y = 5
    enemy_dir = 2
    score = 0

    while True:
        if exit_pressed():
            wait_release()
            led_menu()
            return

        if joy_left():
            player_x -= 3
        elif joy_right():
            player_x += 3

        player_x = max(0, min(118, player_x))

        if select_pressed() and bullet_y == -1:
            bullet_x = player_x + 5
            bullet_y = 50
            beep(1800, 0.012)

        if bullet_y != -1:
            bullet_y -= 4

            if bullet_y < 0:
                bullet_y = -1

        enemy_x += enemy_dir

        if enemy_x <= 0 or enemy_x >= 118:
            enemy_dir *= -1
            enemy_y += 3

        if bullet_y != -1:
            hit_x = enemy_x <= bullet_x <= enemy_x + 10
            hit_y = enemy_y <= bullet_y <= enemy_y + 6

            if hit_x and hit_y:
                score += 1
                beep(1200, 0.035)
                led_score()

                bullet_y = -1
                enemy_x = random.randint(0, 110)
                enemy_y = 5

                if enemy_dir > 0:
                    enemy_dir += 1
                else:
                    enemy_dir -= 1

        if enemy_y >= 52:
            game_over(score)
            return

        oled.fill(0)
        oled.text(str(score), 0, 0)

        oled.fill_rect(player_x, 56, 10, 5, 1)
        oled.pixel(player_x + 5, 54, 1)

        oled.fill_rect(enemy_x, enemy_y, 10, 6, 1)
        oled.pixel(enemy_x + 2, enemy_y + 2, 0)
        oled.pixel(enemy_x + 7, enemy_y + 2, 0)

        if bullet_y != -1:
            oled.vline(bullet_x, bullet_y, 4, 1)

        oled.show()
        time.sleep(0.04)

# ================== START ==================
splash()

# ================== MAIN LOOP ==================
while True:
    draw_menu()

    if time.ticks_diff(time.ticks_ms(), last_move) > 220:
        if menu_up_pressed():
            menu_index -= 1

            if menu_index < 0:
                menu_index = len(games) - 1

            beep(850, 0.015)
            last_move = time.ticks_ms()

        elif menu_down_pressed():
            menu_index += 1

            if menu_index >= len(games):
                menu_index = 0

            beep(850, 0.015)
            last_move = time.ticks_ms()

    if select_pressed():
        beep(1300, 0.04)
        wait_release()

        led_playing()

        oled.fill(0)
        draw_frame()
        center_text("LOADING", 22)
        center_text(games[menu_index]["name"], 38)
        oled.show()
        time.sleep(0.45)

        if menu_index == 0:
            snake_game()
        elif menu_index == 1:
            pong_game()
        elif menu_index == 2:
            catch_game()
        elif menu_index == 3:
            flappy_game()
        elif menu_index == 4:
            invaders_game()

    time.sleep(0.025)
