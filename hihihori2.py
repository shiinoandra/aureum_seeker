import math
import re
from os.path import abspath
from os import path
import pyautogui
import random
import time
from bezier import Curve  
import numpy as np

import csv
from datetime import datetime
import os

import undetected_chromedriver as uc  # Alternative to regular Chrome driver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

class RaidHelper:
    
    def __init__(self,driver):
        self.driver=driver
        self.log_filename = datetime.today().strftime('%Y-%m-%d')+"_raid_log.html"
        self._initialize_log_file()


    def _initialize_log_file(self):
            """Creates a styled HTML log file with a table header if it doesn't exist."""
            # If the file already exists, we do nothing.
            if os.path.exists(self.log_filename):
                return
                
            print(f"[i] Log file not found. Creating '{self.log_filename}'...")
            # Create the HTML file with a header and some CSS for styling
            with open(self.log_filename, 'w', encoding='utf-8') as f:
                f.write("""<!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>GBF Raid Loot Log</title>
                        <style>
                            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; color: #333; }
                            h1 { text-align: center; color: #1d2129; }
                            table { border-collapse: collapse; width: 95%; margin: 20px auto; box-shadow: 0 2px 8px rgba(0,0,0,0.1); background-color: #fff; }
                            th, td { border: 1px solid #ddd; text-align: left; padding: 12px; vertical-align: middle; }
                            thead { background-color: #4267B2; color: white; }
                            tr:nth-child(even) { background-color: #f2f2f2; }
                            tr:hover { background-color: #e9ebee; }
                            .loot-cell { display: flex; flex-wrap: wrap; align-items: center; }
                            .loot-item { display: inline-block; text-align: center; position: relative; margin: 4px; }
                            .loot-item img { width: 48px; height: 48px; border-radius: 4px; }
                            .loot-item .quantity { position: absolute; bottom: -2px; right: -2px; background-color: rgba(0,0,0,0.75); color: white; border-radius: 6px; padding: 2px 5px; font-size: 11px; font-weight: bold; }
                        </style>
                    </head>
                    <body>
                        <h1>GBF Raid Loot Log</h1>
                        <table>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Raid ID</th>
                                    <th>Raid Name</th>
                                    <th>Loot Collected</th>
                                </tr>
                            </thead>
                            <tbody>
                            </tbody>
                        </table>
                    </body>
                    </html>""")

    def play_alert_sound(self, sound_file="alert.mp3"):
        """
        Plays a sound file to alert the user.
        """
        try:
            # Check if the sound file exists before trying to play it
            if os.path.exists(sound_file):
                print("[!!!] PLAYING CAPTCHA ALERT SOUND [!!!]")
                playsound(sound_file)
            else:
                print(f"[!] Alert sound file not found at '{sound_file}'")
        except Exception as e:
            print(f"[!] Error playing sound. Make sure 'playsound' is installed correctly.")
            print(f"[!] Details: {e}")

    @staticmethod
    def bezier_curve(start, end, steps=25):
        """
        Calculates the points for a Bezier curve and returns them as a list of tuples.
        """
        # Use the same logic as before to generate control points
        dx, dy = end[0] - start[0], end[1] - start[1]
        control1 = (
            start[0] + dx * random.uniform(0.2, 0.4) + random.uniform(-dx*0.1, dx*0.1),
            start[1] + dy * random.uniform(0.2, 0.4) + random.uniform(-dy*0.1, dy*0.1)
        )
        control2 = (
            start[0] + dx * random.uniform(0.6, 0.8) + random.uniform(-dx*0.1, dx*0.1),
            start[1] + dy * random.uniform(0.6, 0.8) + random.uniform(-dy*0.1, dy*0.1)
        )
        
        nodes = np.asfortranarray([
            [start[0], control1[0], control2[0], end[0]],
            [start[1], control1[1], control2[1], end[1]],
        ])
        
        curve = Curve(nodes, degree=3)
        
        # Evaluate the curve at 'steps' number of points
        points_on_curve = curve.evaluate_multi(np.linspace(0, 1, steps))
        
        # Return as a list of (x, y) tuples
        return list(zip(points_on_curve[0], points_on_curve[1]))
        
    def click_element(self, element):
        win_position = self.driver.get_window_rect()
        offset_x = win_position['x']
        offset_y = win_position['y'] + self.driver.execute_script("return window.outerHeight - window.innerHeight;")
        try:
            # First, just ensure the element is in the viewport. 'nearest' is less robotic.
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'nearest', inline: 'nearest'});", element
            )
            time.sleep(random.uniform(0.1, 0.3)) # Pause as if to locate the element

            # Add a small, random "adjustment" scroll. Humans rarely stop perfectly.
            scroll_offset = random.randint(-30, 30)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_offset});")
            time.sleep(random.uniform(0.2, 0.4)) # A final pause before moving the mouse

        except Exception as e:
            print(f"[!] scrollIntoView failed: {e}")

        rect = self.get_element_rect(element)

        center_x = rect["x"] + rect["width"] / 2 + offset_x
        center_y = rect["y"] + rect["height"] / 2 + offset_y

        sigma_x = rect["width"] * 0.2
        sigma_y = rect["height"] * 0.2

        x = random.gauss(center_x, sigma_x)
        y = random.gauss(center_y, sigma_y)

        # Get start and end positions
        start_pos = pyautogui.position()
        end_pos = (x, y)

         # 1. Define total duration and number of steps for the movement
        total_duration = random.uniform(0.1, 0.3)
        num_steps = 10

        # 2. Get the list of all points along the curve
        points = RaidHelper.bezier_curve(start_pos, end_pos, steps=num_steps)

        # 3. Calculate the duration for each individual step
        duration_per_step = total_duration / num_steps

        # 4. Loop through the points and move with a calculated duration (NO time.sleep)
        for i, point in enumerate(points):
            # Calculate progress (from 0.0 to 1.0)
            progress = i / num_steps
            # Apply the sine easing function
            ease_value = (math.sin(math.pi * progress - math.pi / 2) + 1) / 2
            
            # The middle of the movement should be fastest, ends should be slowest.
            # We distribute the total duration according to the ease curve.
            # This is a bit abstract, a simpler way is to just vary the duration.
            
            # A simpler but still effective approach:
            # Make the start and end of the movement slower.
            if progress < 0.2 or progress > 0.8:
                step_duration = duration_per_step * 1.5 # 50% slower
            else:
                step_duration = duration_per_step * 0.75 # 25% faster
        
            pyautogui.moveTo(point[0], point[1], duration=step_duration)

        # Add tiny "correction" movements at the end for more realism
        for _ in range(random.randint(1, 3)):
            pyautogui.move(
                random.randint(-2, 2),
                random.randint(-2, 2),
                duration=random.uniform(0.01, 0.03)
            )

        # Click with a variable hold time
        hold_time = random.uniform(0.07, 0.1)
        pyautogui.mouseDown()
        time.sleep(hold_time)
        pyautogui.mouseUp()
        
    def perform_browse_scrolling(self):
        """
        With a random probability, performs a series of up/down scrolls
        to simulate a human browsing the list before making a choice.
        """
        # Only perform this "browsing" simulation sometimes (e.g., 60% of the time)
        if random.random() < 0.6:
            print("[i] Simulating human-like 'browse' scrolling...")
            
            # Decide on a random number of scrolls to perform
            num_scrolls = random.randint(2, 5)
            
            for i in range(num_scrolls):
                # Scroll a random amount (positive is down, negative is up)
                scroll_amount = random.randint(250, 600)
                if random.random() < 0.5: # 50% chance to scroll up
                    scroll_amount *= -1
                    
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                
                # Pause between scrolls, as if reading
                time.sleep(random.uniform(0.4, 0.9))
            
            # A final scroll back towards the top to reset the view
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(0.3, 0.6))

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

            # List of keywords to check for (all in lowercase)
            captcha_keywords = ["verification", "verify", "captcha"]
            # Check if any of the keywords are in the lowercased popup text
            if any(keyword in popup_text.lower() for keyword in captcha_keywords):
                result = "captcha"
            # --- END OF IMPROVEMENT ---
            elif "This raid battle is full" in popup_text:
                result = "raid_full"
            elif "You don’t have enough AP" in popup_text or "not enough AP" in popup_text.lower():
                result = "not_enough_ap"
            elif "You can only provide backup in up to three raid battles at once." in popup_text:
                result = "three_raid"
            elif "Check your pending battles." in popup_text:
                result = "toomuch_pending"
            elif "This raid battle has already ended" in popup_text:
                result = "ended"
            else:
                result = "unknown_popup"

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

            self.perform_browse_scrolling()



            raid_rooms = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div#prt-search-list div.btn-multi-raid.lis-raid.search")
                )
            )
            
            eligible_raids = []
            HP_THRESHOLD = 30
            for raid in raid_rooms:
                try:
                    hp_style = raid.find_element(By.CSS_SELECTOR, ".prt-raid-gauge-inner").get_attribute("style")
                    hp_percent = float(hp_style.split("width:")[1].split("%")[0])
                    
                    if hp_percent >= HP_THRESHOLD:
                        # Instead of acting immediately, add the valid raid to our list of choices
                        eligible_raids.append({"hp": hp_percent, "raid_element": raid})
                except (NoSuchElementException, IndexError):
                    continue
            
            if not eligible_raids:
                 print("[i] No raids met the HP threshold. Skipping.")
                 return "skip"

            target_raid = random.choice(eligible_raids)
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
                    try:
                        fallback_tab_btn = self.driver.find_element(By.CSS_SELECTOR, ".icon-supporter-type-7")
                        self.click_element(fallback_tab_btn)
                    except:
                        return("error")

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
                raid_name = raids[0].find_element(By.CSS_SELECTOR, ".txt-raid-name").text.strip()
                self.see_battle_result_by_id(raid_id,raid_name)
                
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
    

    def log_raid_results(self, raid_id, raid_name):
            """Scrapes loot and writes it as a new row in the HTML log file."""
            print(f"[i] Logging results for raid {raid_id} to HTML...")
            try:
                loot_container = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".prt-item-list"))
                )
                loot_items = loot_container.find_elements(By.CSS_SELECTOR, ".lis-treasure.btn-treasure-item")
                
                if not loot_items:
                    print("[i] No loot items found to log.")
                    return

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 1. Build the HTML string for all loot items in this raid
                loot_html_parts = []
                for item in loot_items:
                    try:
                        img_element = item.find_element(By.CSS_SELECTOR, ".img-treasure-item")
                        item_id = img_element.get_attribute("alt")
                        item_image_url = img_element.get_attribute("src")
                        
                        quantity = 1
                        try:
                            count_element = item.find_element(By.CSS_SELECTOR, ".prt-article-count")
                            quantity_text = count_element.text.strip().replace('x', '')
                            if quantity_text:
                                quantity = int(quantity_text)
                        except NoSuchElementException:
                            pass # Quantity remains 1

                        # Create a styled div for each item with a quantity overlay
                        loot_html_parts.append(f"""
                            <div class="loot-item">
                                <img src="{item_image_url}" alt="ID: {item_id}" title="Item ID: {item_id}">
                                <span class="quantity">x{quantity}</span>
                            </div>""")
                    except (NoSuchElementException, StaleElementReferenceException) as e:
                        print(f"[!] Could not process a loot item, skipping it: {e}")

                loot_html_string = "".join(loot_html_parts)

                # 2. Build the full HTML table row for this raid entry
                new_row_html = f"""
                <tr>
                    <td>{timestamp}</td>
                    <td>{raid_id}</td>
                    <td>{raid_name}</td>
                    <td class="loot-cell">{loot_html_string}</td>
                </tr>"""

                # 3. Read the existing log, insert the new row, and write it back
                with open(self.log_filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Insert the new row just before the closing <tbody> tag
                content = content.replace("</tbody>", new_row_html + "\n</tbody>")
                
                with open(self.log_filename, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"[✓] Successfully logged {len(loot_items)} item type(s) for raid {raid_id}.")

            except TimeoutException:
                print("[!] Loot container '.prt-item-list' not found. Nothing to log.")
            except Exception as e:
                print(f"[!!] An unexpected error occurred during HTML loot logging: {e}")

        
    def see_battle_result_by_id(self,raid_id,raid_name):
        print(f"[→] Opening result for raid {raid_id}")
        selector = f"#prt-unclaimed-list .btn-multi-raid.lis-raid[data-raid-id='{raid_id}']"
        battle_elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        self.click_element(battle_elem)

        # Process result
        try:
            result_ok_btn = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".btn-usual-ok"))
            )
            self.click_element(result_ok_btn)
            time.sleep(random.uniform(0.2, 0.7))
            self.log_raid_results(raid_id,raid_name)

            self.driver.back()

            # Wait until we’re back to the pending list
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#prt-unclaimed-list .btn-multi-raid.lis-raid"))
            )
            print(f"[✓] Finished raid {raid_id}")

        except Exception as e:
            print(f"[!] Error processing raid {raid_id}: {e}")
            return "next"

# --- Main script execution ---
try:
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")


    driver = uc.Chrome(
        options=chrome_options,
        user_data_dir=r"C:\\Selenium\\ChromeProfile" # Use 'r' for raw string to avoid path issues
    )
    rh = RaidHelper(driver)
    rh.clean_raid_queue()

    # Main loop
    for i in range(1000):
        emergency_exit=False
        status = rh.pick_raid()

        if status == "next":
            if rh.select_summmon() == "next":
                if rh.join_raid() == "next":
                    rh.do_raid() # Final step, loop continues regardless of outcome
                    think_time = random.uniform(2, 5) # 5 to 12 seconds
                    print(f"[i] Raid cycle complete. Simulating 'think time' for {think_time:.2f} seconds...")
                    time.sleep(think_time)
        elif status == "toomuch_pending":
            rh.clean_raid_queue()
        elif status == "three_raid":
            print("Three raids joined, waiting before refresh...")
            time.sleep(random.uniform(15, 40))
            rh.refresh_raid_list()
        elif status == "captcha":
            print("CAPTCHA detected. Stopping script.")
            rh.play_alert_sound() # Play the alert sound
            emergency_exit=True
            break
        elif status in ["skip", "error", "raid_full", "not_enough_ap","ended", "unknown_popup"]:
            print(f"Status is '{status}'. Refreshing and retrying.")
            rh.refresh_raid_list()
            time.sleep(random.uniform(1, 3))
        else:
            print(f"Unhandled status: '{status}'. Stopping.")
            break
finally:
    print("[i] Script finished or was interrupted.")
    if driver:
        print("[i] Closing browser...")
        driver.quit()
