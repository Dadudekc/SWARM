from unittest.mock import MagicMock

moveTo = MagicMock()
click = MagicMock()
write = MagicMock()
press = MagicMock()
position = MagicMock(return_value=(0, 0))
size = MagicMock(return_value=(1920, 1080))
screenshot = MagicMock()
getActiveWindow = MagicMock()
