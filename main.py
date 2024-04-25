import json
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys
import asyncio
import threading


# Read username and password from logindata.txt
with open("logindata.txt", "r") as file:
        username = file.readline().strip()
        password = file.readline().strip()

# Set up ChromeDriver
chrome_driver_path = "/home/ccw100/.local/lib/python3.10/site-packages/chromedriver_py/chromedriver_linux64"
chrome_options = Options()
#chrome_options.add_argument("--start-maximized")  # Maximize the browser window
chrome_driver_service = Service(chrome_driver_path)

# Initialize WebDriver
driver = webdriver.Chrome(service=chrome_driver_service, options=chrome_options)

# Open the website
driver.get("https://www.discord.com/login")
wait = WebDriverWait(driver, 60)

#Initialize cookies
f = "/home/ccw100/discordbot/cookies/discord_cookies.json"
if open(f).read() != "":
    print(open(f).read())
    cookies = json.load(open(f))
    # Add each cookie to the WebDriver session
    for cookie in cookies:
        driver.add_cookie(cookie)
    
    #Reload the website to auto authenticate
    driver.get("https://www.discord.com/login")
    wait = WebDriverWait(driver, 60)

#Attempt to load cookies
if open(f).read() == "":
    #Were there no cookies?
    #Authenticate

    # Find username and password input fields by ID
    username_field = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@aria-label="Email or Phone Number"]')))
    password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))

    # Enter username and password
    username_field.send_keys(username)
    password_field.send_keys(password)

    time.sleep(1)
    # Find and click the login button by class name
    login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".marginBottom8_ce1fb9.button__5573c.button__581d0.lookFilled__950dd.colorBrand__27d57.sizeLarge_b395a7.fullWidth_fdb23d.grow__4c8a4")))
    login_button.click()
    print(f"Logging in as {username}")

parent_element = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.XPATH, '//ul[@aria-label="Direct Messages"]')))
print("Authentication successful")

# Find all list items inside the parent element
list_items = parent_element.find_elements(By.TAG_NAME, 'li')
list_items = list_items[2:]

print("Avaialble dms: ")
# Iterate over each list item and print its text
for item in list_items:
        print(item.text)

messageboxinput = None
recipientname = ""

async def check_new_message(driver):
    print("Listening for  messages...")
    chat_messages_element = WebDriverWait(driver, 86400).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-list-id="chat-messages"]')))
            
    # Get the initial count of <li> elements
    initial_count = len(chat_messages_element.find_elements(By.TAG_NAME, 'li'))
                            
    while True:
        try:
            # Wait until a new <li> element is appended to chat_messages_element
            WebDriverWait(driver, 86400).until(
                lambda driver: len(chat_messages_element.find_elements(By.TAG_NAME, 'li')) > initial_count
                                                                        )
                                                
            # Get the new <li> elements
            new_messages = chat_messages_element.find_elements(By.TAG_NAME, 'li')[initial_count:]
                                                                        
            # Print the text of each new <li> element
            for message in new_messages:
                print("New Message:", message.text)
                                                                                                                                    
            # Update the initial count for the next iteration
            initial_count = len(chat_messages_element.find_elements(By.TAG_NAME, 'li'))
        except Exception as e:
            print("Error:", e)
            print(traceback.format_exc())

def run_check_new_message(driver):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(check_new_message(driver))


async def main(driver):
    while True:
        print("Enter command: ", end="")
        command = input()
        if command.startswith("dm"): #Trying to open a dm:
            channel = command.split("dm ")[1]
            element = None
            for item in list_items:
                if item.text == channel:
                    element = item
                    break
            if element == None:
                print("Invalid")
                continue
            print("Opening dm to " + channel)
            element.click()
            recipientname = channel
            threading.Thread(target=run_check_new_message, args=(driver,), daemon=True).start()


            print("Listening for messages...")

        elif command.startswith("msg") and recipientname != "":
            #data-slate-node is always the same regardless of whethter there is text in the box, whatever the textbox is is dynamically changed... for some reason
            #however it will always be the first childs child element of this
            messageboxinput = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-slate-node="text"]'))).find_element(By.XPATH, './*/*[1]')
            message = command.split("msg ")[1]
            messageboxinput.send_keys(message)
            #html element for text input updates too often and requires enter to be seperate from other key presses to avoid bot detection
            messageboxinput = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-slate-node="text"]'))).find_element(By.XPATH, './*/*[1]')
            messageboxinput.send_keys(Keys.RETURN)
            print(f"Sent {message} to {recipientname}")
        else:
            print("Invalid command " + command)

# Usage example
async def run_main(driver):
    await main(driver)

def save_cookies(driver, file_path):
    try: # Get all cookies from the current WebDriver session
        cookies = driver.get_cookies()
                                    
        # Save cookies to a file
        with open(file_path, 'w') as f:
            json.dump(cookies, f)
                                                                            
            print("Cookies saved successfully.")
    except Exception as e:
        print("Error:", e)
save_cookies(driver, "/home/ccw100/discordbot/cookies/discord_cookies.json")

# Call the main asynchronous function
asyncio.run(run_main(driver))
