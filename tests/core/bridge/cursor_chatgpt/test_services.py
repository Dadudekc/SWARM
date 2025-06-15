import types
from tools.core.bridge.cursor_chatgpt.driver import DriverManager
from tools.core.bridge.cursor_chatgpt.scraper import ChatScraperService
import pytest


def test_driver_setup(mocker):
    mock_driver = object()
    mock_chrome = mocker.patch('selenium.webdriver.Chrome', return_value=mock_driver)
    mgr = DriverManager()
    result = mgr.setup()
    assert result is mock_driver
    assert mgr.driver is mock_driver
    mock_chrome.assert_called_once()


class DummyElement:
    def __init__(self, text, href):
        self.text = text
        self._href = href

    def get_attribute(self, name):
        return self._href


def test_scraper_filters_chats(mocker):
    dummy_driver = mocker.Mock()
    dummy_driver.find_elements.return_value = [
        DummyElement('Keep', 'a'),
        DummyElement('Skip', 'b'),
    ]
    mgr = types.SimpleNamespace(driver=dummy_driver)
    scraper = ChatScraperService(mgr, exclusions=['Skip'])
    chats = scraper.get_filtered_chats()
    assert chats == [{'title': 'Keep', 'link': 'a'}]

