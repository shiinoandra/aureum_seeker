import math
import re
from os.path import abspath
from os import path
import pyautogui
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

class RaidHelper:
    
    def __init__(self,driver):
        self.driver=driver
    
    def click_element(self,element):
        win_position = self.driver.get_window_rect()
        offset_x = win_position['x'] 
        offset_y = win_position['y'] + driver.execute_script("return window.outerHeight - window.innerHeight;")
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element
            )
            time.sleep(0.25)
        except Exception as e:
            print(f"[!] scrollIntoView failed: {e}")

        rect = self.get_element_rect(element)
        center_x = rect["x"] + rect["width"] / 2 + offset_x
        center_y = rect["y"] + rect["height"] / 2 + offset_y
        sigma_x = rect["width"] * 0.2
        sigma_y = rect["height"] * 0.2
        x = random.gauss(center_x, sigma_x)
        y = random.gauss(center_y, sigma_y)
        sx, sy = pyautogui.position()
        steps = 12
        for i in range(steps + 1):
            t = i / steps
            ease = 3*t**2 - 2*t**3
            px = sx + (x - sx) * ease
            py = sy + (y - sy) * ease
            pyautogui.moveTo(px, py)
            time.sleep(0.001)
        
        for _ in range(random.randint(2, 4)):
            pyautogui.moveTo(
                x + random.uniform(-2, 2),
                y + random.uniform(-2, 2),
                duration=random.uniform(0.01, 0.03)
            )
        hold_time = random.uniform(0.05, 0.1)
        pyautogui.mouseDown()
        time.sleep(hold_time)
        pyautogui.mouseUp()

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
    
    def handle_popup(self, timeout=1):
        try:
            popup = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".common-pop-error.pop-show"))
            )
            popup_text = popup.find_element(By.CSS_SELECTOR, "#popup-body").text.strip()
            print(f"[!] Popup detected: '{popup_text}'")

            result = "unknown_popup"
            if "This raid battle is full" in popup_text:
                result = "raid_full"
            elif "You don’t have enough AP" in popup_text or "not enough AP" in popup_text.lower():
                result = "not_enough_ap"
            elif "You can only provide backup in up to three raid battles at once." in popup_text:
                result = "three_raid"
            elif "verification" in popup_text:
                result = "captcha"
            elif "Check your pending battles." in popup_text:
                result = "toomuch_pending"
            elif "This raid battle has already ended" in popup_text:
                result = "ended"

            try:
                ok_button = popup.find_element(By.CSS_SELECTOR, ".btn-usual-ok")
                self.click_element(ok_button)
                time.sleep(1.5)
            except Exception:
                print("[!] Could not find OK button to close popup.")
            return result
        except TimeoutException:
            return None
        
    def refresh_raid_list(self):
        try:
            refresh_btn = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".btn-search-refresh")
                    )
                )
            self.click_element(refresh_btn)
        except TimeoutException:
            print("[!] Refresh button not found.")

    def pick_raid(self):
        print("[1] Finding suitable raid...")
        try:
            if "#quest/assist" not in driver.current_url:
                self.driver.get("https://game.granbluefantasy.jp/#quest/assist")
            
            # First, check for popups that might prevent picking a raid
            popup_result = self.handle_popup(timeout=1)
            if popup_result:
                return popup_result

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#prt-search-list"))
            )
            raid_rooms = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div#prt-search-list div.btn-multi-raid.lis-raid.search")
                )
            )
            
            raids_data = []
            HP_THRESHOLD = 30
            for raid in raid_rooms:
                try:
                    hp_style = raid.find_element(By.CSS_SELECTOR, ".prt-raid-gauge-inner").get_attribute("style")
                    hp_percent = float(hp_style.split("width:")[1].split("%")[0])
                    if hp_percent >= HP_THRESHOLD:
                        raids_data.append({"hp": hp_percent, "raid_element": raid})
                except (NoSuchElementException, IndexError):
                    continue
            
            if not raids_data:
                 return "skip"

            target_raid = raids_data[0] # Simplest strategy: pick the first eligible one
            print(f"Target raid found with {target_raid['hp']}% HP.")
            self.click_element(target_raid["raid_element"])

            popup_result = self.handle_popup(timeout=2)
            if popup_result:
                return popup_result
            
            print("[✓] Joined raid successfully.")
            return "next"
        except Exception as e:
            print(f"An error occurred in pick_raid: {e}")
            return "error"

    def find_support_tab_from_elem(self, support_elem):
        try:
            container = support_elem.find_element(
                By.XPATH, "./ancestor::div[contains(@class, 'prt-supporter-attribute')]"
            )
            class_attr = container.get_attribute("class")
            match = re.search(r"type(\d+)", class_attr)
            if not match:
                print(f"[!] Could not detect type class from: {class_attr}")
                return None
            
            support_type = int(match.group(1))
            type_map = {0: 7, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6}
            tab_index = type_map.get(support_type)
            if tab_index is None:
                print(f"[!] No matching tab for type {support_type}")
                return None
            
            print(f"[i] Support type{support_type} → tab button type-{tab_index}")
            tab_selector = f".ico-supporter-type-{tab_index}" # Note: Class name might be different
            return self.driver.find_element(By.CSS_SELECTOR, tab_selector)
        except Exception as e:
            print(f"Error finding support tab: {e}")
            return None

    def select_summmon(self):
        try:
            WebDriverWait(self.driver, 0.7).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,".btn-usual-ok.se-quest-start"))
            )
            print("Auto Summon Setting Found")
            return "next"
        except TimeoutException:
            try:
                # Fallback summon selection logic here
                print("[i] No auto-summon. Selecting fallback summon...")
                fallback_tab_btn = self.driver.find_element(By.CSS_SELECTOR, ".icon-supporter-type-7")
                self.click_element(fallback_tab_btn)
                
                first_summon = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".prt-supporter-attribute.type0 .btn-supporter")
                    )
                )
                self.click_element(first_summon)
                return "next"
            except Exception as e:
                print(f"Error during fallback summon selection: {e}")
                return "error"
        
    def join_raid(self):
        try:
            quest_start_btn = WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR,".btn-usual-ok.se-quest-start"))
            )
            self.click_element(quest_start_btn)
            return "next"
        except TimeoutException:
            print("[!] Could not find quest start button.")
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

    def clean_raid_queue(self):
        try:
            print("[!] Starting pending raid cleanup process...")
            self.driver.get("https://game.granbluefantasy.jp/#quest/assist")
            
            pending_battle_btn = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-unconfirmed-result"))
            )
            self.click_element(pending_battle_btn)
            
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "prt-unclaimed-list"))
            )
            
            while True:
                time.sleep(1.5) # Allow DOM to settle
                raids = self.driver.find_elements(By.CSS_SELECTOR, "#prt-unclaimed-list .btn-multi-raid.lis-raid")
                
                if not raids:
                    print("[✓] No more pending raids found. Cleanup complete.")
                    break
                
                print(f"[i] Found {len(raids)} pending raid(s). Clearing the first one.")
                raid_id = raids[0].get_attribute("data-raid-id")
                self.see_battle_result_by_id(raid_id)
                
            print("[i] Returning to the raid search page.")
            self.driver.get("https://game.granbluefantasy.jp/#quest/assist")
            return "next"

        except TimeoutException:
            print("[i] No 'pending battles' button found. Assuming queue is clear.")
            if "#quest/assist" not in self.driver.current_url:
                self.driver.get("https://game.granbluefantasy.jp/#quest/assist")
            return "next"
        except Exception as e:
            print(f"[!!] An unexpected error occurred during raid cleanup: {e}")
            return "error"
        
    def see_battle_result_by_id(self,raid_id):
        print(f"[→] Opening result for raid {raid_id}")
        selector = f"#prt-unclaimed-list .btn-multi-raid.lis-raid[data-raid-id='{raid_id}']"
        battle_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        self.click_element(battle_elem)

        # Process result
        try:
            result_ok_btn = WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-usual-ok"))
            )
            self.click_element(result_ok_btn)
            time.sleep(random.uniform(0.2, 0.7))

            self.driver.back()

            # Wait until we’re back to the pending list
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#prt-unclaimed-list .btn-multi-raid.lis-raid"))
            )
            print(f"[✓] Finished raid {raid_id}")

        except Exception as e:
            print(f"[!] Error processing raid {raid_id}: {e}")

# --- Main script execution ---
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument(r"user-data-dir=C:\Selenium\ChromeProfile")

chrome_driver_exe_path = abspath("chromedriver.exe")
assert path.exists(chrome_driver_exe_path), 'chromedriver.exe not found!'

service = Service(executable_path=chrome_driver_exe_path)
driver = webdriver.Chrome(service=service, options=chrome_options)
rh = RaidHelper(driver)

# Main loop
for i in range(1000):
    emergency_exit=False
    status = rh.pick_raid()

    if status == "next":
        if rh.select_summmon() == "next":
            if rh.join_raid() == "next":
                rh.do_raid() # Final step, loop continues regardless of outcome
    elif status == "toomuch_pending":
        rh.clean_raid_queue()
    elif status == "three_raid":
        print("Three raids joined, waiting before refresh...")
        time.sleep(random.uniform(15, 40))
        rh.refresh_raid_list()
    elif status == "captcha":
        print("CAPTCHA detected. Stopping script.")
        emergency_exit=True
        break
    elif status in ["skip", "error", "raid_full", "not_enough_ap","ended", "unknown_popup"]:
        print(f"Status is '{status}'. Refreshing and retrying.")
        rh.refresh_raid_list()
        time.sleep(random.uniform(1, 3))
    else:
        print(f"Unhandled status: '{status}'. Stopping.")
        break