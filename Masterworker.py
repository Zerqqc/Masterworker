import cv2
import numpy as np
import pyautogui
import time
import os
import sys
import keyboard
from datetime import datetime

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'resources', relative_path)

reference_images = [
    resource_path("upgrade_1.png"),
    resource_path("upgrade_2.png"),
    resource_path("upgrade_3.png"),
    resource_path("skip.png"),
    resource_path("affix.png"),
    resource_path("reset.png"),
    resource_path("confirm.png")
]

reference_images_gray = [cv2.imread(img, 0) for img in reference_images]

def find_image_on_screen(reference_image_gray):
    screenshot = np.array(pyautogui.screenshot())
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)
    res = cv2.matchTemplate(screenshot_gray, reference_image_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val >= 0.8:
        return (max_loc[0] + reference_image_gray.shape[1] // 2,
                max_loc[1] + reference_image_gray.shape[0] // 2)
    
    return None

def click_at_position(x, y, clicks=1, interval=0.5):
    pyautogui.moveTo(x, y)
    for _ in range(clicks):
        pyautogui.click()
        time.sleep(interval)

def move_cursor_to_center():
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 2, screen_height // 2)

def process_upgrade(upgrade_index, attempt_number, consecutive_successes, fail_count, upgrade_not_found_count):
    upgrade_image = reference_images_gray[upgrade_index]
    
    move_cursor_to_center()
    upgrade_pos = find_image_on_screen(upgrade_image)

    if not upgrade_pos:
        print(f"Upgrade button {upgrade_index + 1} not found")
        upgrade_not_found_count += 1

        if upgrade_not_found_count > 5:
            print("Upgrade button not found too many times. Stopping program.")
            return False, consecutive_successes, fail_count, False, 0, upgrade_not_found_count

        return False, consecutive_successes, fail_count, False, 0, upgrade_not_found_count

    click_at_position(*upgrade_pos, clicks=4, interval=0.2)
    time.sleep(0.2)
    
    skip_pos = find_image_on_screen(reference_images_gray[3])
    if not skip_pos:
        print(f"Attempt {attempt_number} -> Skip button not found")
        return False, consecutive_successes, fail_count, True, 1, upgrade_not_found_count
    
    click_at_position(*skip_pos)
    time.sleep(1)

    affix_pos = find_image_on_screen(reference_images_gray[4])
    if affix_pos:
        consecutive_successes += 1
        print(f"Attempt {attempt_number} -> Success [{consecutive_successes}/3]")
        time.sleep(0.2)
        pyautogui.click()
        return True, consecutive_successes, fail_count, True, 0, upgrade_not_found_count
    else:
        fail_count += 1
        print(f"Attempt {attempt_number} -> Fail [{fail_count}]")
        time.sleep(0.2)
        pyautogui.click()
        
        reset_pos = find_image_on_screen(reference_images_gray[5])
        if not reset_pos:
            print(f"Attempt {attempt_number} -> Reset button not found")
            return False, consecutive_successes, fail_count, True, 0, upgrade_not_found_count
        
        click_at_position(*reset_pos)
        time.sleep(0.2)
        
        confirm_pos = find_image_on_screen(reference_images_gray[6])
        if not confirm_pos:
            print(f"Attempt {attempt_number} -> Confirm button not found")
            return False, consecutive_successes, fail_count, True, 0, upgrade_not_found_count
        
        click_at_position(*confirm_pos)
        time.sleep(0.2)
        return False, 0, fail_count, True, 0, upgrade_not_found_count

def main():
    stop_program = False
    started = False

    def on_key_press(event):
        nonlocal stop_program, started
        if event.name == '`':
            if started:
                stop_program = True
            else:
                started = True

    keyboard.on_press(on_key_press)

    print("Press ` to start the program...")
    keyboard.wait('`')
    time.sleep(0.5)
    print("Process started. Press ` again to stop.")

    attempt_number = 0
    consecutive_successes = 0
    fail_count = 0
    skip_not_found_count = 0
    upgrade_not_found_count = 0

    while not stop_program and consecutive_successes < 3:
        window = pyautogui.getActiveWindow()
        if window is None or "Diablo IV" not in window.title:
            print("Program stopped because the Diablo 4 window is not focused.")
            break

        success, consecutive_successes, fail_count, attempt_made, skip_not_found, upgrade_not_found_count = process_upgrade(
            upgrade_index=0, 
            attempt_number=attempt_number + 1, 
            consecutive_successes=consecutive_successes, 
            fail_count=fail_count, 
            upgrade_not_found_count=upgrade_not_found_count
        )
        
        if attempt_made:
            attempt_number += 1

        if not success and attempt_made:
            consecutive_successes = 0

        skip_not_found_count += skip_not_found
        if skip_not_found_count >= 2:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"Program stopped. (Not enough materials?) - [{current_time}]")
            break

        if success or (not success and not skip_not_found):
            skip_not_found_count = 0

    if consecutive_successes == 3:
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"Item fully masterworked after [{attempt_number}] attempts [{current_time}]")
    elif not stop_program and skip_not_found_count < 3:
        print(f"Number of attempts: {attempt_number}")

    print("Process ended.")

if __name__ == "__main__":
    main()
