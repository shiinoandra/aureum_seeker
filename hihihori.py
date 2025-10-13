from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import math

from os.path import abspath
from os import path

chrome_options = Options()
chrome_options.add_argument("--start-maximized")   # start fullscreen
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("detach", True)  # <- keeps Chrome open

chrome_options.add_argument(r"user-data-dir=C:\\Selenium\\ChromeProfile")
chrome_driver_exe_path = abspath("chromedriver.exe")  # download from https://chromedriver.chromium.org/downloads
assert path.exists(chrome_driver_exe_path), 'chromedriver.exe not found!'


service = Service(executable_path=chrome_driver_exe_path)

driver = webdriver.Chrome(service=service, options=chrome_options)




# 3. Navigate to the raid list page
driver.get("https://game.granbluefantasy.jp/#quest/assist")  # replace with actual URL


raid_rooms = WebDriverWait(driver, 20).until(
    EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "div#prt-search-list div.btn-multi-raid.lis-raid.search")
    )
)

raids_data = []
HP_THRESHOLD = 35
for raid in raid_rooms:

    raid_info = raid.find_element("css selector", ".prt-raid-info")
    raid_id = raid.get_attribute("data-raid-id")

    raid_name = raid_info.find_element(By.CSS_SELECTOR, ".txt-raid-name").get_attribute("innerHTML")
    raid_host = raid_info.find_element(By.CSS_SELECTOR, ".txt-request-name").get_attribute("innerHTML")

    hp_style = raid_info.find_element(By.CSS_SELECTOR, ".prt-raid-gauge-inner").get_attribute("style")
    hp_percent = float(hp_style.split("width:")[1].split("%")[0])

    rect = driver.execute_script("""
                                    const rect = arguments[0].getBoundingClientRect();
                                    return {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height
                                    };
                                """, raid)
    raids_data.append({"id":raid_id,"name": raid_name, "hp": hp_percent, "rect": rect,"host":raid_host})

target_raid = next(r for r in raids_data if r["hp"] >= HP_THRESHOLD)

print(target_raid)

import pyautogui, random, time

win_position = driver.get_window_rect()
offset_x = win_position['x']
offset_y = win_position['y'] + 163  # ~80px for browser chrome toolbar
screen_x = target_raid["rect"]["x"] + offset_x
screen_y = target_raid["rect"]["y"] + offset_y
x = screen_x + random.randint(math.floor((0.2 *target_raid["rect"]["width"])), math.floor((0.85 *target_raid["rect"]["width"])) )
y = screen_y + random.randint(1, math.floor((0.4 *target_raid["rect"]["height"])))
print(offset_x,offset_y,x,y)

pyautogui.moveTo(x, y, duration=random.uniform(0.1, 0.3))
# pyautogui.click()