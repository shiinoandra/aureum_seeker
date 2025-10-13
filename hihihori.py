import math

from os.path import abspath
from os import path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import (
    NoSuchElementException, 
    StaleElementReferenceException
)
import time
import pyautogui, random, time

class RaidHelper:
    
    def __init__(self,driver):
        self.driver=driver
    
    def click_element(self,element):
        win_position = self.driver.get_window_rect()
        offset_x = win_position['x']
        offset_y = win_position['y'] + 160  # ~80px for browser chrome toolbar
        
        if not isinstance(element,dict):    
            try:
                # Scroll into view safely
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element
                )
                time.sleep(0.25)
            except Exception as e:
                print(f"[!] scrollIntoView failed: {e}")

            rect = self.get_element_rect(element)
        else:
            rect = element.get("rect", None)
            if rect is None:
                raise ValueError("Element dictionary must contain a 'rect' key")

            viewport_height = self.driver.execute_script("return window.innerHeight;")
            if rect["y"] + rect["height"]/2 > viewport_height or rect["y"] < 0:
                print("[!] Raid element may be off-screen — scrolling container...")
                # Try to scroll the main raid list (safe fallback)
                try:
                    self.driver.execute_script(
                        "document.querySelector('#prt-search-list').scrollBy(0, arguments[0]);",
                        rect["y"] - viewport_height/2
                    )
                    time.sleep(0.25)
                except Exception as e:
                    print(f"[!] Could not scroll raid list: {e}")
            
        screen_x = rect["x"] + offset_x
        screen_y = rect["y"] + offset_y

        x = screen_x + random.uniform(0.1, 0.4) * rect["width"]
        y = screen_y + random.uniform(0.2, 0.4) * rect["height"]
        
        sx, sy = pyautogui.position()
        #print("moving cursor to:  "+str(x)+","+str(y))
        steps = 5
        for i in range(steps):
            t = i / steps
            px = sx + (x - sx) * (3*t**2 - 2*t**3)
            py = sy + (y - sy) * (3*t**2 - 2*t**3)
            pyautogui.moveTo(px, py, duration=0.01)
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.click()

    def get_element_rect(self,element):
        return  self.driver.execute_script("""
                                            const rect = arguments[0].getBoundingClientRect();
                                            return {
                                                x: rect.x,
                                                y: rect.y,
                                                width: rect.width,
                                                height: rect.height
                                            };
                                        """, element)

    def pick_raid(self):
        print("[1] Finding suitable raid...")
        try:
            self.driver.get("https://game.granbluefantasy.jp/#quest/assist")  # replace with actual URL
            raid_rooms = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div#prt-search-list div.btn-multi-raid.lis-raid.search")
                )
            )

            raids_data = []
            HP_THRESHOLD = 35
            for raid in raid_rooms:
                rect = self.get_element_rect(raid)
                raid_info = raid.find_element("css selector", ".prt-raid-info")
                raid_id = raid.get_attribute("data-raid-id")

                raid_name = raid_info.find_element(By.CSS_SELECTOR, ".txt-raid-name").get_attribute("innerHTML")
                raid_host = raid_info.find_element(By.CSS_SELECTOR, ".txt-request-name").get_attribute("innerHTML")

                hp_style = raid_info.find_element(By.CSS_SELECTOR, ".prt-raid-gauge-inner").get_attribute("style")
                hp_percent = float(hp_style.split("width:")[1].split("%")[0])
                
                raids_data.append({"id":raid_id,"name": raid_name, "hp": hp_percent, "rect": rect,"host":raid_host})

            target_raid = next(r for r in raids_data if r["hp"] >= HP_THRESHOLD)
            if (not target_raid):
                return "skip"
            print("target: "+ str(target_raid))
            self.click_element(target_raid)
            try:
                popup = WebDriverWait(self.driver, 1).until(
                    EC.visibility_of_element_located((By.XPATH, "//*[contains(text(), \"This raid battle is full.\")]"))
                )
                print("[!] Raid is full, handling popup...")
                ok_button = self.driver.find_element(By.CSS_SELECTOR, ".btn-usual-ok")
                ok_button.click()
                time.sleep(1)
                return "skip"  # signal the main loop to pick another raid
            except TimeoutException:
                print("[✓] Joined raid successfully.")
                return "next"
        except Exception as e:
            print("error: "+e)
            return "error"
        

    def find_support_tab_from_elem(self, support_elem):
        # Step 1: find ancestor container
        container = support_elem.find_element(
            By.XPATH, "./ancestor::div[contains(@class, 'prt-supporter-attribute')]"
        )

        # Step 2: get its classes
        class_attr = container.get_attribute("class")
        # Example: "prt-supporter-attribute type3 selected"

        # Step 3: extract the type number
        import re
        match = re.search(r"type(\d+)", class_attr)
        if not match:
            print("[!] Could not detect type class from:", class_attr)
            return
        support_type = int(match.group(1))

        # Step 4: map type → tab index
        type_map = {
            0: 7,  # special case: type0 corresponds to type-7
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            6: 6,
        }
        tab_index = type_map.get(support_type)
        if tab_index is None:
            print(f"[!] No matching tab for type {support_type}")
            return

        print(f"[i] Support type{support_type} → tab button type-{tab_index}")

        # Step 5: find the tab header
        tab_selector = f".icon-supporter-type-{tab_index}"
        tab_button = self.driver.find_element(By.CSS_SELECTOR, tab_selector)

        # Step 6: click it (Selenium or PyAutoGUI fallback)
        return tab_button

    
    def select_summmon(self):
        #check if auto summon pick succeed
        try:
            quest_start_btn = WebDriverWait(self.driver, 0.7).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR,".btn-usual-ok.se-quest-start")
                    )
                )
            if quest_start_btn:
                print("Auto Summon Setting Found")
                return "next"

        except TimeoutException:
            #look for grand order
            try:
                support_level = "Lvl 200"
                support_name = "Grand"

                xpath = f"""
                //div[contains(@class, 'supporter-summon') and
                    .//span[@class='txt-summon-level' and normalize-space(text())='{support_level}'] and
                    .//span[@class='js-summon-name' and normalize-space(text())='{support_name}']]
                """
                support_elems = driver.find_elements(By.XPATH, xpath)
                if support_elems: 
                    attribute_tab_btn = self.find_support_tab_from_elem(support_elems[0])
                    self.click_element(attribute_tab_btn)
                    self.click_element(support_elems[0])
                else:
                    print("[!] Desired summon not found — using first summon in type0.")
                    # Step 1: Click type0’s tab (mapped to icon-supporter-type-7)
                    fallback_tab_btn = self.driver.find_element(By.CSS_SELECTOR, ".icon-supporter-type-7")
                    self.click_element(fallback_tab_btn)

                    # Step 2: Find the first summon in type0 list
                    first_summon = WebDriverWait(self.driver, 0.5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".prt-supporter-attribute.type0 .btn-supporter")
                        )
                    )

                    print("[→] Selecting first available summon...")
                    self.click_element(first_summon)
                return "next"

            except Exception as e:
                print("Error during summon selection:", e)
                return "error"
        
    def join_raid(self):
        try:
            quest_start_btn = WebDriverWait(self.driver, 1).until(
                    EC.visibility_of_element_located(
                        (By.CSS_SELECTOR,".btn-usual-ok.se-quest-start")
                    )
                )
            if quest_start_btn:
                self.click_element(quest_start_btn)
                return "next"
        except TimeoutException:
            return "error"
        
    def do_raid(self):
        try:
            # Wait until the attack button is visible and ready
            atk_btn_visible = WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".btn-attack-start.display-on")
                )
            )
            print("[✓] Attack button visible")

            start_time = time.time()
            while time.time() - start_time < 80:

                # If button still active, click full auto
                try:
                    fullauto_btn = WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ".btn-auto"))
                    )
                    self.click_element(fullauto_btn)
                    print("[⚙] Full Auto clicked")
                except TimeoutException:
                    print("[!] Full Auto not found, skipping...")
                # Refresh to process the next step
                time.sleep(0.2)
                try:
                    atk_btn = self.driver.find_element(By.CSS_SELECTOR, ".btn-attack-start")
                    class_attr = atk_btn.get_attribute("class")

                    # Check if the turn has processed (button went off)
                    if "display-off" in class_attr:
                        print("[→] Turn processed — exiting attack loop")
                        return "next"

                except (NoSuchElementException, StaleElementReferenceException):
                    print("[!] Attack button not found — retrying...")
                    return "next"
                self.driver.refresh()
                time.sleep(1.25)

        except TimeoutException:
            print("[×] Timeout waiting for attack button — probably not in battle")
            return "error"





chrome_options = Options()
chrome_options.add_argument("--start-maximized")   # start fullscreen
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("detach", True)  # <- keeps Chrome open

chrome_options.add_argument(r"user-data-dir=C:\\Selenium\\ChromeProfile")
chrome_driver_exe_path = abspath("chromedriver.exe")  # download from https://chromedriver.chromium.org/downloads
assert path.exists(chrome_driver_exe_path), 'chromedriver.exe not found!'


service = Service(executable_path=chrome_driver_exe_path)

driver = webdriver.Chrome(service=service, options=chrome_options)
rh = RaidHelper(driver)
steps = [
            rh.pick_raid,
            rh.select_summmon,
            rh.join_raid,
            rh.do_raid
        ]


for i in range (5):
    for step in steps:
        status = step()
        if status!="next":
            print("failed, exiting")
            break
        if status =="skip":
            continue
        


