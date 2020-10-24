from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
from datetime import datetime
import json

from random import random

filename = "data.json"
filename_login = "login.json"
random_time = 0.5
selenium_chrome_url = "http://10.0.0.10:4444/wd/hub"


def load_page(driver: webdriver.Remote):
    driver.get("https://pos.hawk-hhg.de/")
    time.sleep(random() * random_time)


def login(driver: webdriver.Remote, login_data: dict):
    input_elements = driver.find_elements_by_class_name("input_login")
    for input_element in input_elements:
        element_type = input_element.get_attribute("type")
        if element_type == "text":
            input_element.send_keys(login_data["username"])
        elif element_type == "password":
            input_element.send_keys(login_data["password"])
    submit_button = driver.find_element_by_class_name("submit")
    time.sleep(random() * random_time)
    submit_button.click()


def logout(driver: webdriver.Remote):
    elements = driver.find_element_by_class_name("divloginstatus").find_elements_by_class_name("links3")
    for element in elements:
        if element.tag_name == "a" and element.get_attribute("accesskey") == "l":
            time.sleep(random() * random_time)
            element.click()
            break


def logged_in(driver: webdriver.Remote) -> bool:
    element = driver.find_element_by_class_name("divloginstatus")
    elements = element.find_elements_by_class_name("links3")
    is_logged_in = len(elements) > 5
    print(f"currently logged {'in' if is_logged_in else 'out'}")
    return is_logged_in


def go_to_grades(driver: webdriver.Remote):
    print(driver.current_url)
    selector = "#makronavigation > ul > li:nth-child(2) > a"
    driver.find_element_by_css_selector(selector).click()
    print(driver.current_url)
    time.sleep(random() * random_time)
    selector = "#wrapper > div.divcontent > div.content_max_portal_qis > div > form > div > ul > li:nth-child(5) > a"
    driver.find_element_by_css_selector(selector).click()
    print(driver.current_url)
    time.sleep(random() * random_time)
    selector = "#wrapper > div.divcontent > div.content > form > ul > li > a:nth-child(3)"
    driver.find_element_by_css_selector(selector).click()
    print(driver.current_url)
    time.sleep(random() * random_time)


def row_to_data(row: WebElement):
    cols = row.find_elements_by_tag_name("td")
    if len(cols) == 0:
        return None
    grade = cols[3].text.strip()
    nr = int(cols[0].text.strip())
    data = {
        "nr": nr,
        "text": cols[1].text.strip(),
        "semester": cols[2].text.strip(),
        "grade": grade.replace(",", "."),
        "status": cols[4].text.strip(),
        "credits": cols[5].text.strip(),
        "note": cols[6].text.strip(),
        "try": cols[7].text.strip(),
        "date": datetime.strptime(cols[8].text.strip(), "%d.%m.%Y").date().isoformat()
    }
    return data


def get_grades(driver: webdriver.Remote):
    tbody = driver.find_elements_by_tag_name("tbody")[1]
    rows = tbody.find_elements_by_tag_name("tr")
    entries = [row_to_data(row) for row in rows]
    entries = [entry for entry in entries if entry]
    return entries


def load_grades():
    try:
        with open(filename, "r") as file:
            grades = json.load(file)
            print(f"loaded: {grades}")
            return grades
    except FileNotFoundError:
        print("file not found")
    return []


def save_grades(grades):
    try:
        with open(filename, "w") as file:
            json.dump(grades, file)
            print(f"saved: {grades}")
            return grades
    except IOError:
        print("error saving")


def new_entries(old, new):
    return [entry for entry in new if entry not in old]


def main():
    driver = None
    grades = load_grades()
    grades_new = []
    try:
        driver = webdriver.Remote(selenium_chrome_url, DesiredCapabilities.CHROME)
        load_page(driver)
        if not logged_in(driver):
            try:
                with open(filename_login, "r") as file:
                    login_data = json.load(file)
                    login(driver, login_data)
            except FileNotFoundError:
                print(f"file not found: {filename_login}, please provide login data")
                with open(filename_login, "w") as file:
                    json.dump({"username": "", "password": ""}, file)

        if logged_in(driver):
            go_to_grades(driver)
            grades_new = get_grades(driver)
            grades_diff = new_entries(grades, grades_new)
            print(f"diff: {grades_diff}")
            save_grades(grades_new)
            print(grades)
            logout(driver)
        else:
            print("couldn't log in")
        logged_in(driver)

    except WebDriverException:
        print("web driver exception")
    finally:
        driver.close()
    return grades_new


if __name__ == '__main__':
    main()
