from unittest.mock import MagicMock

Window = MagicMock()
getActiveWindow = MagicMock(return_value=Window())
