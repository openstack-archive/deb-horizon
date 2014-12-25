#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import selenium.common.exceptions as Exceptions
from selenium.webdriver.support import expected_conditions
import selenium.webdriver.support.ui as Support
from selenium.webdriver.support import wait


class BaseWebObject(object):
    """Base class for all web objects."""
    def __init__(self, driver, conf):
        self.driver = driver
        self.conf = conf
        self.explicit_wait = self.conf.selenium.explicit_wait

    def _is_element_present(self, *locator):
        try:
            self._get_element(*locator)
            return True
        except Exceptions.NoSuchElementException:
            return False

    def _is_element_visible(self, *locator):
        try:
            return self._get_element(*locator).is_displayed()
        except (Exceptions.NoSuchElementException,
                Exceptions.ElementNotVisibleException):
            return False

    def _get_element(self, *locator):
        return self.driver.find_element(*locator)

    def _get_elements(self, *locator):
        return self.driver.find_elements(*locator)

    def _fill_field_element(self, data, field_element):
        field_element.clear()
        field_element.send_keys(data)
        return field_element

    def _select_dropdown(self, value, element):
        select = Support.Select(element)
        select.select_by_visible_text(value)

    def _select_dropdown_by_value(self, value, element):
        select = Support.Select(element)
        select.select_by_value(value)

    def _turn_off_implicit_wait(self):
        self.driver.implicitly_wait(0)

    def _turn_on_implicit_wait(self):
        self.driver.implicitly_wait(self.conf.selenium.page_timeout)

    def _wait_till_text_present_in_element(self, locator, text):
        condition = expected_conditions.text_to_be_present_in_element(locator,
                                                                      text)
        try:
            wait.WebDriverWait(self.driver, self.explicit_wait).\
                until(condition)
        except Exceptions.TimeoutException:
            return False
        return True
