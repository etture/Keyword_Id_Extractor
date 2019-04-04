from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import re


class wait_for_attribute_value_regex(object):
    def __init__(self, locator, attribute, regex):
        self.locator = locator
        self.attribute = attribute
        self.regex = regex

    def __call__(self, driver):
        try:
            element_attribute = EC._find_element(driver, self.locator).get_attribute(self.attribute)
            return re.match(self.regex, element_attribute)
        except StaleElementReferenceException:
            return False
