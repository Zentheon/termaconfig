# termaconfig/exceptions.py

class TableTypeError(Exception):
    """Raised when a terminaltables class instance is invalid"""
    pass

class ConfigValidationError(Exception):
    """Raised by the TermaConfig class when an errortree exists (invalid config)"""
    pass
