import json
import time
from base64 import b64decode
from datetime import datetime
from random import random

from discord_webhook import DiscordWebhook
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webelement import WebElement, By
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

setting_users = "users"
setting_username = "username"
setting_password = "password"
setting_discord_id = "discord_id"
setting_webdriver_type = "webdriver_type"
setting_webdriver_url = "remote_webdriver_url"
setting_browser_binary = "browser_binary"
setting_webdriver_binary = "webdriver_binary"
setting_random_time = "random_wait_time"
setting_webhook = "discord_webhook"
setting_webhook_url = "url"
setting_webhook_name = "name"
setting_webhook_avatar = "avatar_url"
setting_base64 = "pw_base64"
setting_include_grades = "include_grades"
setting_id = "id"
setting_local_notification = "local_notification"

webdriver_type_remote = "remote"
webdriver_type_local_chrome = "chrome-local"
webdriver_type_local_firefox = "firefox-local"
webdriver_type_local_edge = "edge-local"

filename_data = "data_{}.json"
filename_settings = "settings.json"
random_time = 1

webdriver_setting_mapping = {
    "Chrome": webdriver_type_local_chrome,
    "Edge": webdriver_type_local_edge,
    "Firefox": webdriver_type_local_firefox,
    "Remote": webdriver_type_remote
}

log = print


class SettingsMissingException(Exception):
    pass


def load_page(driver: webdriver.Remote):
    driver.get("https://pos.hawk.de/")
    time.sleep(random() * random_time)


def login(driver: webdriver.Remote, user: dict):
    input_elements = driver.find_elements(by=By.CLASS_NAME, value="input_login")
    for input_element in input_elements:
        element_type = input_element.get_attribute("type")
        if element_type == "text":
            input_element.send_keys(user[setting_username])
        elif element_type == "password":
            input_element.send_keys(user[setting_password])
    submit_button = driver.find_element(by=By.CLASS_NAME, value="submit")
    time.sleep(random() * random_time)
    submit_button.click()


def logout(driver: webdriver.Remote):
    login_div = driver.find_element(by=By.CLASS_NAME, value="divloginstatus")
    elements = login_div.find_elements(by=By.CLASS_NAME, value="links3")
    for element in elements:
        if element.tag_name == "a" and element.get_attribute("accesskey") == "l":
            time.sleep(random() * random_time)
            element.click()
            break


def logged_in(driver: webdriver.Remote) -> bool:
    element = driver.find_element(by=By.CLASS_NAME, value="divloginstatus")
    elements = element.find_elements(by=By.CLASS_NAME, value="links3")
    is_logged_in = len(elements) > 5
    log(f"logged {'in' if is_logged_in else 'out'}")
    return is_logged_in


def go_to_grades(driver: webdriver.Remote):
    selector = "#makronavigation > ul > li:nth-child(2) > a"
    driver.find_element(by=By.CSS_SELECTOR, value=selector).click()
    time.sleep(random() * random_time)
    selector = "#wrapper > div.divcontent > div.content_max_portal_qis > div > form > div > ul > li:nth-child(5) > a"
    driver.find_element(by=By.CSS_SELECTOR, value=selector).click()
    time.sleep(random() * random_time)
    selector = "#wrapper > div.divcontent > div.content > form > ul > li > a:nth-child(3)"
    driver.find_element(by=By.CSS_SELECTOR, value=selector).click()
    time.sleep(random() * random_time)


def row_to_data(row: WebElement) -> dict:
    cols = row.find_elements(by=By.TAG_NAME, value="td")
    if len(cols) == 0:
        return {}
    try:
        grade = cols[3].text.strip()
        nr = int(cols[0].text.strip())
        date_text = cols[8].text.strip()
        date = None
        try:
            if len(date_text) > 0:
                date = datetime.strptime(date_text, "%d.%m.%Y").date().isoformat()
        finally:
            pass
        data = {
            "nr": nr,
            "text": cols[1].text.strip(),
            "semester": cols[2].text.strip(),
            "grade": grade.replace(",", "."),
            "status": cols[4].text.strip(),
            "credits": cols[5].text.strip(),
            "note": cols[6].text.strip(),
            "try": cols[7].text.strip(),
            "date": date
        }
        return data
    except Exception as e:
        log(f"Error extracting data from row:\n\n{e}")


def get_grades(driver: webdriver.Remote) -> list:
    tbody = driver.find_elements(by=By.TAG_NAME, value="tbody")[1]
    rows = tbody.find_elements(by=By.TAG_NAME, value="tr")
    entries = [row_to_data(row) for row in rows]
    entries = [entry for entry in entries if entry]
    return entries


def load_grades(user_id: str) -> list:
    try:
        with open(filename_data.format(user_id), "r") as file:
            grades = json.load(file)
            return grades
    except FileNotFoundError:
        log("file not found")
    return []


def save_grades(grades, user_id: str):
    try:
        with open(filename_data.format(user_id), "w") as file:
            json.dump(grades, fp=file, separators=(',', ':'), indent=1)
            return grades
    except IOError:
        log("error saving")


def new_entries(old: list, new: list) -> list:
    return [entry for entry in new if entry not in old]


def notify_plyer(text):
    from plyer import notification
    notification.notify(
        title="HAWK POS",
        message=text,
        timeout=10
    )


def handle_diff(entries: list, settings: dict, user: dict, notify=notify_plyer):
    if not entries:
        return
    username = user[setting_username]
    discord_id = user[setting_discord_id] if setting_discord_id in user else None
    include_grades = user[setting_include_grades]
    webhook_settings = user[setting_webhook]

    text_list = [f"**{entry['text']}**{': {}'.format(entry['grade']) if include_grades and entry['grade'] else ''}"
                 for entry in entries]
    text = "Updates:\n{}".format(',\n'.join(text_list))
    mention = None if not discord_id else f"@{discord_id}" if discord_id in ["everyone", "here"] else f"<@{discord_id}>"
    if not webhook_settings:
        webhook_settings = settings[setting_webhook]
    if webhook_settings['url']:
        webhook = DiscordWebhook(webhook_settings)
        webhook.webhook_post_embed("POS", text, url="https://pos.hawk.de", footer=username, content=mention)
    if settings[setting_local_notification]:
        text_list = [f"{entry['text']}{': {}'.format(entry['grade']) if include_grades and entry['grade'] else ''}"
                     for entry in entries]
        text = "Updates:\n{}".format(',\n'.join(text_list))
        notify(text)


def load_settings() -> dict:
    with open(filename_settings, "r") as file:
        settings = json.load(file)
        if not (setting_users in settings and setting_webhook in settings and
                (setting_webdriver_url in settings or setting_webdriver_type in settings)):
            raise SettingsMissingException(f"settings are missing, please edit {filename_settings}")
        if setting_random_time in settings:
            global random_time
            random_time = settings[setting_random_time]
        if setting_base64 not in settings:
            settings[setting_base64] = False
        if setting_webdriver_type not in settings:
            settings[setting_webdriver_type] = webdriver_type_remote
        if setting_local_notification not in settings:
            settings[setting_local_notification] = False
        return settings


def save_settings(settings: dict):
    with open(filename_settings, "w") as file:
        json.dump(settings, fp=file, indent=2)


def default_settings():
    return {
        setting_users: [{setting_username: "",
                         setting_password: "",
                         setting_discord_id: ""}],
        setting_webdriver_url: "http://127.0.0.1:4444/wd/hub",
        setting_webdriver_type: webdriver_type_local_chrome,
        setting_random_time: random_time,
        setting_webhook: {setting_webhook_url: "",
                          setting_webhook_name: "",
                          setting_webhook_avatar: ""},
        setting_base64: False,
        setting_local_notification: True
    }


def create_settings():
    save_settings(default_settings())


def main(notify=notify_plyer):
    try:
        settings = load_settings()
        for user in settings[setting_users]:
            driver = None
            try:
                if settings[setting_base64]:
                    user[setting_password] = b64decode(user[setting_password]).decode()
                if setting_id not in user:
                    user[setting_id] = user[setting_username]
                if setting_include_grades not in user:
                    user[setting_include_grades] = False
                if setting_webhook not in user:
                    user[setting_webhook] = settings[setting_webhook]
                grades = load_grades(user[setting_id])
                driver = None
                if settings[setting_webdriver_type] == webdriver_type_remote:
                    options = webdriver.ChromeOptions()
                    driver = webdriver.Remote(settings[setting_webdriver_url], options=options)
                elif settings[setting_webdriver_type] == webdriver_type_local_firefox:
                    options = webdriver.FirefoxOptions()
                    options.add_argument("-headless")
                    if setting_browser_binary in settings:
                        options.binary_location = settings[setting_browser_binary]
                    service_options = {}
                    if setting_webdriver_binary in settings:
                        service_options['executable_path'] = settings[setting_webdriver_binary]
                        service = FirefoxService(**service_options)
                    else:
                        service = FirefoxService(GeckoDriverManager().install())
                    driver = webdriver.Firefox(
                        service=service,
                        options=options
                    )
                elif settings[setting_webdriver_type] == webdriver_type_local_chrome:
                    options = webdriver.ChromeOptions()
                    options.add_argument("--headless")
                    if setting_browser_binary in settings:
                        options.binary_location = settings[setting_browser_binary]
                    service_options = {}
                    if setting_webdriver_binary in settings:
                        service_options['executable_path'] = settings[setting_webdriver_binary]
                        service = ChromeService(**service_options)
                    else:
                        service = ChromeService(ChromeDriverManager().install())
                    driver = webdriver.Chrome(
                        service=service,
                        options=options
                    )
                elif settings[setting_webdriver_type] == webdriver_type_local_edge:
                    options = webdriver.EdgeOptions()
                    options.add_argument("--headless")
                    service = EdgeService(EdgeChromiumDriverManager().install())
                    driver = webdriver.Edge(
                        service=service,
                        options=options
                    )
                driver.implicitly_wait(1)
                load_page(driver)
                if not logged_in(driver):
                    login(driver, user)
                else:
                    break
                if logged_in(driver):
                    go_to_grades(driver)
                    grades_new = get_grades(driver)
                    grades_diff = new_entries(grades, grades_new)
                    save_grades(grades_new, user[setting_id])
                    if grades:
                        handle_diff(grades_diff, settings, user, notify)
                    else:
                        log("first run, not handling new entries")
                    log(f"entries: loaded {len(grades)}, saved {len(grades_new)}, {len(grades_diff)} changes")
                    time.sleep(3)
                    logout(driver)
                    logout_tries = 1
                    while logout_tries <= 5 and logged_in(driver):
                        logout(driver)
                        logout_tries += 1
                        time.sleep(2)
                else:
                    log("couldn't log in")
                logged_in(driver)
                driver.delete_all_cookies()
                driver.quit()
                driver = None
                time.sleep(2)
            except WebDriverException as wde:
                log(f"web driver exception:\n{wde}")
            finally:
                if driver:
                    try:
                        driver.quit()
                    except WebDriverException:
                        pass
    except FileNotFoundError:
        create_settings()
        log(f"please provide settings in {filename_settings}")


if __name__ == '__main__':
    main()
