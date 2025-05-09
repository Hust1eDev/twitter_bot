import os
import pickle
import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd

class Parser:
    def __init__(self, proxy=None, proxy_username=None, proxy_password=None):
        self.cookies_file = 'cookies.pkl'
        self.driver = None
        self.proxy = proxy
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        
    def setup_driver(self):
        """Настройка и инициализация драйвера"""
        chrome_options = Options()

        chrome_options.add_argument("--disable-blink-features")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument("--user-data-dir=chrome-data")
        
        # Настройка прокси через selenium-wire
        seleniumwire_options = None
        if self.proxy:
            proxy_url = f"socks5://{self.proxy_username}:{self.proxy_password}@{self.proxy}"
            seleniumwire_options = {
                'proxy': {
                    'http': proxy_url,
                    'https': proxy_url,
                    'no_proxy': 'localhost,127.0.0.1'
                }
            }

        self.driver = webdriver.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )
        self.driver.maximize_window()
        
        # Выполняем антидетект скрипт
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        '''
        })
        
    def save_cookies(self):
        """Сохранение куки в файл"""
        if self.driver:
            pickle.dump(self.driver.get_cookies(), open(self.cookies_file, "wb"))
            
    def load_cookies(self):
        """Загрузка куки из файла"""
        if os.path.exists(self.cookies_file):
            cookies = pickle.load(open(self.cookies_file, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            return True
        return False
    
    def login(self, url, username, password):
        """Авторизация на сайте"""
        if not self.driver:
            self.setup_driver()
            
        self.driver.get(url)
        
        # Если есть сохраненные куки, пробуем их использовать
        if self.load_cookies():
            self.driver.refresh()
            # Проверяем, что авторизация прошла успешно
            # Здесь нужно добавить проверку на успешную авторизацию
            print("Авторизация прошла успешно")
            return
            
        # Если куки нет или они не работают, выполняем ручную авторизацию
        try:
            
            # Ждем успешной авторизации
            time.sleep(5)
            print("Авторизация прошла успешно")
            # Сохраняем куки после успешной авторизации
            self.save_cookies()
            
        except Exception as e:
            print(f"Ошибка при авторизации: {e}")
            
    def parse_data(self, wallet_data):
        """Метод для парсинга данных"""
        # Здесь реализуйте вашу логику парсинга
        
        time.sleep(5)
        
        # делаем первый поиск
        search_field = self.driver.find_element(By.XPATH, '''//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[2]/div/div[2]/div/div/div/div/div[1]/div/div/div/form/div[1]/div/div/div/div/div[2]/div/input''')
        search_field.send_keys("1")
        search_field.send_keys(Keys.ENTER)
        
        time.sleep(5)
        
        # Добавляем счетчик итераций
        iteration_counter = 1
        
        for wallet_address, amount in wallet_data:
            # Обработка суммы: убираем запятые и дробную часть
            amount_str = str(amount).replace(",", "")
            if "." in amount_str:
                amount_str = amount_str.split(".")[0]
            
            # Конвертируем в число
            amount_value = int(amount_str)
            
            # Пропускаем, если сумма больше 500000
            if amount_value > 500000:
                print(f"#{iteration_counter} Пропускаем адрес {wallet_address} с суммой {amount_value} (больше 500000)")
                iteration_counter += 1
                continue
                
            search_field = self.driver.find_element(By.XPATH, '''//*[@id="react-root"]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]/div[1]/div[1]/div/div/div/div/div[2]/div[2]/div/div/div/form/div[1]/div/div/div/div/div[2]/div/input''')
            time.sleep(1)
            
            actions = ActionChains(self.driver)
            actions.click(search_field)
            actions.key_down(Keys.COMMAND).send_keys("a").key_up(Keys.COMMAND)
            actions.send_keys(Keys.BACKSPACE)
            actions.perform()
            time.sleep(1)
            
            search_field.send_keys(wallet_address)
            search_field.send_keys(Keys.ENTER)
            
            time.sleep(5)
            
            try:
                elements = self.driver.find_elements(By.XPATH, '//*[@aria-label="Timeline: Search timeline"]')
                if not elements:
                    with open('output.csv', 'a', encoding='utf-8') as f:
                        f.write(f'#{iteration_counter} address: {wallet_address} : {0}\n')
                        print(f'#{iteration_counter} address: {wallet_address} : {0}')
                        
                    time.sleep(1)
                else:
                    res = elements[0].find_element(By.XPATH, './*').find_elements(By.XPATH, './*')
                    with open('output.csv', 'a', encoding='utf-8') as f:
                        f.write(f'#{iteration_counter} address: {wallet_address} : {len(res)-1}\n')
                        print(f'#{iteration_counter} address: {wallet_address} : {len(res)-1}')
                        
            except Exception as e:
                print(f'#{iteration_counter} error: {e}')
            
            # Увеличиваем счетчик после обработки каждого кошелька
            iteration_counter += 1
            
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()

    
    def read_wallet_addresses(self, csv_file):
        """
        Read data from the first two columns of a CSV file.
        Returns a list of tuples: (first_column_value, second_column_value)
        """
        # Проверяем существование файла
        if not os.path.exists(csv_file):
            print(f"Файл {csv_file} не существует.")
            return []
            
        try:
            # Читаем только две первые колонки
            df = pd.read_csv(csv_file, usecols=[0, 1])
            
            # Проверим, что обе колонки есть
            if df.shape[1] < 2:
                print("CSV file does not contain at least two columns.")
                return []
            
            # Преобразуем в список кортежей
            two_columns = list(df.itertuples(index=False, name=None))
            return two_columns

        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return []
            
            
def main():
    # Настройка прокси из файла
    try:
        with open('proxy.txt', 'r') as proxy_file:
            proxy_line = proxy_file.read().strip()
            # Формат строки: username:password@address:port
            if '@' in proxy_line:
                auth, proxy = proxy_line.split('@', 1)
                if ':' in auth:
                    proxy_username, proxy_password = auth.split(':', 1)
                else:
                    proxy_username = auth
                    proxy_password = ''
            else:
                proxy = proxy_line
                proxy_username = None
                proxy_password = None
    except FileNotFoundError:
        print("Файл proxy.txt не найден. Используются значения по умолчанию.")
        proxy = None
        proxy_username = None
        proxy_password = None
    
    parser = Parser(
        proxy=proxy,
        proxy_username=proxy_username,
        proxy_password=proxy_password
    )
    
    parser.login(url="https://x.com/home", username="", password="")
    
    # читаем файл с кошельками
    wallet_data = parser.read_wallet_addresses('input.csv') # Замените на csv файл с кошельками
    
    if not wallet_data:
        print("No wallet addresses found in the CSV file or error reading the file.")
        return
    
    try:
        parser.parse_data(wallet_data)
        
    finally:
        parser.close()

if __name__ == "__main__":
    main() 