from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import requests
import telebot
import schedule
import time
import pickle
from datetime import datetime

class AnyEc:
    """ Use with WebDriverWait to combine expected_conditions
        in an OR.
    """
    def __init__(self, *args):
        self.ecs = args
    def __call__(self, driver):
        for fn in self.ecs:
            try:
                res = fn(driver)
                if res:
                    return res
                    # Or return res if you need the element found
            except:
                pass


def cookies_loading(driver):
    """ Returns list of loaded cookies
    """
    for cookie in pickle.load(open('session','rb')):
        driver.add_cookie(cookie)

    cookies_loaded_storage = driver.get_cookies()

    return cookies_loaded_storage

def cookies_savingfresh(driver, cookies_loaded_storage):
    cookies_final_storage = driver.get_cookies()

    cookies_fresh = []

    # take new cookies
    for cookie in cookies_final_storage:
        if cookie not in cookies_loaded_storage:
            cookies_fresh.append(cookie)

    # add old to new without duplicates (cookies integrity)
    fresh_names = []
    for cookie in cookies_fresh:
        fresh_names.append(cookie['name'])

    for cookie in cookies_loaded_storage:
        if cookie['name'] not in fresh_names:
            cookies_fresh.append(cookie)

    pickle.dump(cookies_fresh, open('session','wb'))

    return True


def request_comp(driver, userAgent):
    # get cookies for post request (we can use local cookies)
    cookies = driver.get_cookies()

    for dict in cookies:
        if dict['name'] == 'R3ACTLB':
            R3ACTLB_cookies = dict['name'] + '=' + dict['value'] 
        if dict['name'] == 'XSRF-TOKEN':
            XSRFTOKEN_cookies = dict['name'] + '=' + dict['value']
        if dict['name'] == 'laravel_session':
            laravelsession_cookies = dict['name'] + '=' + dict['value']

    cookie = R3ACTLB_cookies + '; ' + XSRFTOKEN_cookies + '; ' + laravelsession_cookies

    # get token
    search = driver.find_element(By.NAME, 'csrf-token')
    token_row = search.get_attribute('outerHTML')
    token = token_row[33:-2]

    # post request composition
    bizz_data = {
        '_token': token
    }
    bizz_header = {
        'Host': 'hidden-domain.com',
        'User-Agent': userAgent,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Length': '47',
        'Origin': 'https://hidden-domain.com',
        'Connection': 'keep-alive',
        'Referer': 'https://hidden-domain.com/login/stats/business',
        'Cookie': cookie,
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-GPC': '1',
        'TE': 'trailers'
    }

    bizz = requests.post('https://hidden-domain.com/api_user/get_m_bizz',data=bizz_data,headers=bizz_header)

    return bizz

def extract_bizz():
    userAgent = UserAgent().chrome
    options = Options()
    options.headless = True
    options.add_argument(f'user-agent={userAgent}')

    driver = webdriver.Chrome(options=options)
    URL = 'https://hidden-domain.com/login'
    timeout = 70

    # LOGIN page
    driver.get(URL)

    cookies_loaded_storage = cookies_loading(driver)

    driver.refresh 

    try:
        res = WebDriverWait(driver, timeout).until(AnyEc(EC.presence_of_element_located((By.ID, 'username')), EC.presence_of_element_located((By.XPATH, "//div[@class='ucp--content']"))))

        try: # if ucp--content
            res.find_element(By.XPATH, "//div[@class='ucp--content']")
            authorized = True
        except NoSuchElementException: # if username
            authorized = False

    except TimeoutException:
        print("Timed out waiting for login page", flush=True)
        driver.quit()
        return 0

    if not authorized:
        # print('NOT AUTHORIZED')
        search = driver.find_element(By.ID, 'username')
        search.send_keys("Nick_Name")
        search = driver.find_element(By.ID, 'password')
        search.send_keys("password")
        search = driver.find_element(By.ID, 'select_server_1')
        search.send_keys(Keys.RETURN)

        search = driver.find_element(By.ID, 'auth')
        search.send_keys(Keys.RETURN)

        # UCP page
        try:
            res = WebDriverWait(driver, timeout).until(AnyEc(EC.presence_of_element_located((By.XPATH, "//div[@class='ucp--content']")), EC.presence_of_element_located((By.XPATH, "//div[@class='auth-warning-window']//p[text()='Вы точно не робот? Обнови-ка страничку']"))))

            try: # if ucp--content
                res.find_element(By.XPATH, "//div[@class='ucp--content']")

                print('NOT AUTHORIZED: UCP CONTENT', flush=True)

                cookies_savingfresh(driver, cookies_loaded_storage)

                # DATA EXTRACTING
                bizz = request_comp(driver, userAgent)
                driver.quit()
            except NoSuchElementException: # if auth-warning-window
                print('NOT AUTHORIZED: A ROBOT', flush=True)
                return 0
                # ACTIONS TO DODGE DETECTION
                search.send_keys(Keys.RETURN)
                time.sleep(1)
                search.send_keys(Keys.RETURN)
                time.sleep(1)
                search.send_keys(Keys.RETURN)

                time.sleep(40)
                cookies_savingfresh(driver, cookies_loaded_storage)
                
                #DATA EXTRACTING
                bizz = request_comp(driver, userAgent)
                driver.quit()
                
        except TimeoutException:
            print("Timed out waiting for ucp page", flush=True)
            date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")
            driver.save_screenshot(f"./screens/{date}.png")
            driver.quit()
            return 0
    else:
        cookies_savingfresh(driver, cookies_loaded_storage)

        # DATA EXCTRACTING
        bizz = request_comp(driver, userAgent)
        driver.quit()

    try:
        return bizz.json()
    except ValueError:
        # print("Server sent not JSON file / JSON conversion error", flush=True)
        return 0


#
# TeleBot
#
API_KEY = 'your_bot_token'
bot = telebot.TeleBot(API_KEY)

def bizz_get_job(id):
    tries = 0; maxtries = 3
    success = False

    while (tries < maxtries):
        tries = tries + 1
        bizzJson = extract_bizz()

        if bizzJson != 0:
            success = True
            break

    if success:
        bizDict_arr = bizzJson['callback']['bizz']
        mybiz_bProducts_num = bizDict_arr[16]['bProducts']

        if mybiz_bProducts_num < 2000:
            bot.send_message(id, mybiz_bProducts_num)
    else:   
        bot.send_message(id, "Fail after 3 attempts to retrieve data. Look at the log")

IDADMIN = id_tg # is the only user
schedule.every().hour.at(":03").do(bizz_get_job, id=IDADMIN) # id = [list]
# schedule.every(3).minutes.do(bizz_get_job, id=IDADMIN)
SCH_ENABLED = False

@bot.message_handler(commands=["start"])
def bizz_schedule(message):
    global SCH_ENABLED

    if message.chat.id == IDADMIN: # admin
        if not SCH_ENABLED:
            bot.send_message(IDADMIN, "Bot has been activated")
            SCH_ENABLED = True

            while True:
                if SCH_ENABLED:
                    schedule.run_pending()
                    time.sleep(1)
                else:
                    break
        else:
            bot.send_message(message.chat.id, 'Bot is already enabled!')

@bot.message_handler(commands=["stop"])
def bizz_stop(message):
    if message.chat.id == IDADMIN: # admin
        global SCH_ENABLED

        SCH_ENABLED = False

        bot.send_message(message.chat.id, 'Bot was stopped')

bot.infinity_polling(timeout=70, long_polling_timeout = 70)
