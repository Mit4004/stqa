from selenium import webdriver
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()
driver.maximize_window()


def login_test(test_name, username, password):

    driver.get("https://www.saucedemo.com/")

    driver.find_element(By.ID, "user-name").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "login-button").click()

    time.sleep(1)

    if "inventory" in driver.current_url:
        print(test_name + ": Login Successful")
    else:
        print(test_name + ": Login Failed")


login_test(
    "Test Case 1",
    "standard_user",
    "secret_sauce"
)

login_test(
    "Test Case 2",
    "wrong_user",
    "secret_sauce"
)

login_test(
    "Test Case 3",
    "standard_user",
    "wrong_password"
)

login_test(
    "Test Case 4",
    "wrong_user",
    "wrong_password"
)
login_test(
    "Test Case 5",
    "performance_glitch_user",
    "secret_sauce"
)

login_test(
    "Test Case 6",
    "wrong_user",
    "wrong_passwor5478d"
)
login_test(
    "Test Case 7",
    "hellow_world",
    "wrong_password7456"
)
login_test(
    "Test Case 8",
    "locked_out_user",
    "secret_sauce"
)



driver.quit()