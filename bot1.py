import telebot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import pdfkit  # Library for converting HTML to PDF

# Bot and site configuration
TELEGRAM_BOT_TOKEN = '7965054944:AAFXWBNdd7VZ81O9kZvabUjY0XYwAECMFP8'
SITE_LOGIN_URL = 'https://app.creditrepaircloud.com/'
SITE_USERNAME = 'rafalskanastia@gmail.com'
SITE_PASSWORD = 'Ringo123'
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Path to wkhtmltopdf
config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')

# Словарь с именами и Telegram-контактами менеджеров
manager_contacts = {
    "Aleksei Kodatenko RP": "@Aleksei_Ke",
    "Alexander Megas CM": "@Megker",
    "Alexander Balabanov RP": "@anmaverick",
    "Alexandra Belova CM": "@Olivka_Pendergast",
    "Alina Kolpakova": "@alinakolp22",
    "Andrii Labunets RP": "@labunets_a",
    "Arkady Osokin CM": "@arkadyxion",
    "Dmytro Chernukha CM": "@Mrkotuk",
    "Eugene Kuzmenko RP": "@EugeneKuzmenko",
    "Georgii Shepeliakov RP": "@atternol",
    "Kolya Solomennyi CM": "@solomennyii",
    "Lilia Leshenko RP": "@LiliaLeshenko",
    "Mark Tarytsanu CM": "@Benglad2",
    "Maryna Urvantseva": "@Marinee_life",
    "Mykyta Flink RP": "@thenikitamma",
    "Nataliia Grek CM": "@NataliGrekk",
    "Nataliia Denisenko CM": "@dnv987",
    "Nazarii Kramar CM": "@k_rama_r",
    "Nebojsa Connor": "@djseanparker",
    "Nikita Shakotko CM": "@Nikita_El_Diavola",
    "Nikita Yagunov CM": "@ElQwanto",
    "Olga Meshcheryakova CM": "@Olga_mes",
    "Rusla Dawydenko CM": "@vooyager_1",
    "Tony Zhidkov RP LNs": "@azhidkov22",
    "Vladimir Krystal RP": "@crishtalb",
    "Vladyslav Shkilarov CM": "@Vlad_dko",
    # Имена без контактов
    "Julia Krendeleva RP LNs": None,
    "Nataliia Regush CM": None,
}

# Функция для получения имени менеджера с сайта
def scrape_website_for_manager_name(client_name):
    chrome_options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=chrome_options)
    print(f"Opening website: {SITE_LOGIN_URL}")

    try:
        driver.get(SITE_LOGIN_URL)

        # Вход в систему
        print("Waiting for login fields to appear...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="username"]')))
        driver.find_element(By.XPATH, '//*[@id="username"]').send_keys(SITE_USERNAME)
        driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(SITE_PASSWORD)
        driver.find_element(By.XPATH, '//*[@id="signin"]').click()

        # Переход на страницу "Clients"
        print("Waiting for Clients page to load...")
        WebDriverWait(driver, 10).until(EC.url_changes(SITE_LOGIN_URL))
        driver.get('https://app.creditrepaircloud.com/app/clients')

        # Поиск клиента
        print("Waiting for search field to appear...")
        search_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'tableSearch'))
        )
        search_field.send_keys(client_name)
        time.sleep(5)

        # Получение ссылки на клиента
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        found = False
        client_name_lower = client_name[:5].lower()
        for elem in soup.find_all(attrs={"title": True}):
            title_text = elem['title'].lower()
            if client_name_lower in title_text:
                print(f"Found client with name {elem['title']}")
                href = elem.get('href', '')
                if href:
                    driver.get(href)
                    found = True
                    break

        if not found:
            print(f"Client with name {client_name[:5]} not found.")
            return None

        # Извлечение имени менеджера
        print("Waiting for client's Dashboard page to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="root"]/div[2]/div[2]/div/div/div[4]/div/div/div/div/div/div/div/div[1]/h6'))
        )
        manager_name_element = driver.find_element(By.XPATH,
                                                   '//*[@id="root"]/div[2]/div[2]/div/div/div[4]/div/div/div/div/div/div/div/div[1]/h6')
        manager_name = manager_name_element.text
        print(f"Manager Name: {manager_name}")

        return manager_name

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        driver.quit()


# Обработчик сообщений
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def handle_group_message(message):
    # Проверка, упомянут ли бот в сообщении
    if f"@{bot.get_me().username}" in message.text:
        try:
            # Извлечение имени клиента после упоминания бота
            text_parts = message.text.split(f"@{bot.get_me().username}")
            if len(text_parts) > 1:
                client_name = text_parts[1].strip()
                bot.send_message(message.chat.id, f"Searching for client: {client_name}. Please wait...")

                # Поиск имени менеджера
                manager_name = scrape_website_for_manager_name(client_name)
                if manager_name:
                    contact = manager_contacts.get(manager_name)
                    if contact:
                        bot.send_message(message.chat.id, f"{manager_name} {contact}")
                    else:
                        bot.send_message(message.chat.id, manager_name)
                else:
                    bot.send_message(message.chat.id, f"Client {client_name} not found or an error occurred.")
        except Exception as e:
            bot.send_message(message.chat.id, "An error occurred while processing your request.")
            print(f"Error: {e}")

# Запуск бота
try:
    print("Bot started.")
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Error: {e}")
