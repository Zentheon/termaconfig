# termaconfig/__init__.py

__name__ = "termaconfig"
__version__ = "1.0.1"
__authors__ = ["Zentheon <zentheon@mailbox.org>"]
__license__ = "GPL-3.0"

import io
import logging as log

from configobj import ConfigObj
from configobj.validate import Validator

from termaconfig.configtables import ConfigTables
from termaconfig.errortree import ErrorTree
from termaconfig.exceptions import ConfigValidationError, TableTypeError
from termaconfig.parser import ConfigParser
from termaconfig.utils import preprocess_config

# Access the main classes from package root
ConfigValidationError = ConfigValidationError
TableTypeError = TableTypeError

# All valid options should be initialized with None
REQUIRED_SEC_KEYS = ["title", "header", "type", "wrap", "parent", "spacer", "ignore", "toggle"]
REQUIRED_PARAM_KEYS = [
    "default",
    "type",
    "min",
    "max",
    "error",
    "missing",
    "title",
    "note",
    "ignore",
]


class TermaConfig(ConfigObj):
    def __init__(self, config_file, spec_file, **kwargs):
        config_file, spec_file = self.validate_files(config_file, spec_file)

        config_lines = preprocess_config(config_file)
        spec_lines = preprocess_config(spec_file)
        super().__init__(config_lines, configspec=spec_lines)
        # This is how we access the config options after letting ConfigObj initialize
        config = self.__dict__["parent"]

        result = config.validate(Validator(), preserve_errors=True)

        parser = ConfigParser(config, config.configspec, result)
        self.metaconf = parser.metaconf

        self.errortree = ErrorTree(
            self.metaconf,
            include_missing=kwargs.get("include_missing", True),
            include_valid=kwargs.get("include_valid", False),
        )
        if not self.errortree.valid:
            if kwargs.get("logging", False):
                for line in self.errortree.get_tree.splitlines():
                    log.log(log.INFO + 3, line)
            else:
                print(self.errortree.get_tree)

            raise ConfigValidationError(f"The configuration at {config_file} failed validation")

        config_tables = ConfigTables(self.metaconf, config, tabletype=kwargs.get("tabletype", None))
        self.tabledata = config_tables.tabledata

        if config_tables.all_tables:
            if kwargs.get("logging", False):
                log.log(log.INFO + 3, "")
                for line in config_tables.all_tables.splitlines():
                    log.log(log.INFO + 3, line)
            else:
                print()
                print(config_tables.all_tables)

    def validate_files(self, config_file, spec_file):
        if isinstance(config_file, str):
            try:
                config_file = open(config_file, "r")
            except FileNotFoundError:
                raise FileNotFoundError(f"Config file not found: {config_file}")
            except PermissionError:
                raise PermissionError(f"Failed opening config file: {spec_file}")
        if isinstance(spec_file, str):
            try:
                spec_file = open(spec_file, "r")
            except FileNotFoundError:
                raise FileNotFoundError(f"Specification file not found: {spec_file}")
            except PermissionError:
                raise PermissionError(f"Failed opening specification file: {spec_file}")

        if not isinstance(config_file, io.TextIOBase):
            raise TypeError(
                f"Input config is neither a filepath nor filedata object: {config_file}"
            )
        if not isinstance(spec_file, io.TextIOBase):
            raise TypeError(
                f"Input specification is neither a filepath nor filedata object: {spec_file}"
            )

        return config_file, spec_file
