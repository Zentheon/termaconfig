# tests/utils.py

import re
import io
import termaconfig as tc

from printree import ptree

from configobj import ConfigObj
from configobj.validate import Validator

class TermaConfigTests(ConfigObj):
    """Cut-down version of the ZC wrapper for testing"""
    def __init__(self, config_file, spec_file, **kwargs):
        config_file, spec_file = self.validate_files(config_file, spec_file)

        config_lines = tc.preprocess_config(config_file)
        spec_lines = tc.preprocess_config(spec_file)
        super().__init__(config_lines, configspec=spec_lines)
        # This is how we access the config options after letting ConfigObj initialize
        config = self.__dict__['parent']

        self.result = config.validate(Validator(), preserve_errors=True)

        parser = tc.ConfigParser(config, config.configspec, self.result)
        self.metaconf = parser.metaconf

    def validate_files(self, config_file, spec_file):
        if isinstance(config_file, str):
            try: config_file = open(config_file, 'r')
            except FileNotFoundError:
                raise FileNotFoundError(f"Config file not found: {config_file}")
            except PermissionError:
                raise PermissionError(f"Failed opening config file: {spec_file}")
        if isinstance(spec_file, str):
            try: spec_file = open(spec_file, 'r')
            except FileNotFoundError:
                raise FileNotFoundError(f"Specification file not found: {spec_file}")
            except PermissionError:
                raise PermissionError(f"Failed opening specification file: {spec_file}")

        if not isinstance(config_file, io.TextIOBase):
            raise TypeError(f"Input config is neither a filepath nor filedata object: {config_file}")
        if not isinstance(spec_file, io.TextIOBase):
            raise TypeError(f"Input specification is neither a filepath nor filedata object: {spec_file}")

        return config_file, spec_file

def regex_test_lines(input_string, regex_list):
    lines = input_string.splitlines()
    results = []

    if len(lines) != len(regex_list):
            raise ValueError("The number of lines and regex expressions must be the same.")

    for line, regex in zip(lines, regex_list):
        print(line, regex)
        if re.fullmatch(regex, line):
            results.append((line, True))
        else:
            results.append((line, False))

    return results

def load_config(config_path, spec_path):

    # Load configuration and validate it against the spec
    config = ConfigObj(config_path, configspec=spec_path)
    vtor = Validator()
    result = config.validate(vtor, preserve_errors=True)

    return config, result
