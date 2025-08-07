# tests/test_example_set.py

import pytest
from terminaltables3 import AsciiTable
import printree as pt

import zenconfig as zc

from tests.utils import ZenConfigTests, load_config, regex_test_lines

# Paths to test files and spec files
CONFIG_PATH_1 = 'tests/valid-configs/example-config.toml'
SPEC_PATH_1 = 'tests/valid-configs/example-spec.toml'

# Regex. Some pointers:
# AsciiTable should be used for tests for simplicity.
# Always match potential variable whitespace.
# Escape pipe characters. (That one got me)
# Line count has to be the same as the table.

INFO_SEC_REGEX = [
    r'\+General Info.*',
    r'\| Name\s+\| zenconfig\s+\|',
    r'\| Description\s+\| Custom configuration settings.\s+\|',
    r'\+.*'
]
BASIC_SEC_REGEX = [
    r'\+Basic Config.*',
    r'\| Option\s+\| Value\s+\|',
    r'\+.*',
    r'\| Option 1\s+\| eggs, bacon, pancakes, waffles\s+\|',
    r'\| Option 2\s+\| super_custom_value\s+\|',
    r'\| Secondary settings:\s+\|\s+\|',
    r'\| Port\s+\| 3021\s+\|',
    r'\| Address\s+\| 174.192.0.34\s+\|',
    r'\+.*'
]
ADVANCED_SEC_REGEX = [
    r'\+Advanced Config.*',
    r'\| Option\s+\| Value\s+\| Note\s+\|',
    r'\+.*',
    r'\| Enabled\s+\| False\s+\|\s+\|',
    r'\| Items\s+\| Electric guitars, Synthesizers\s+\| You can also add notes\s+\|',
    r'\|\s+\| Hi-hats, Kick drums\s+\| to various entries!\s+\|',
    r'\|\s+\| Studio equipment\.\.\.\s+\|\s+\|',
    r'\+.*'
]

def test_valid_config_set_001():
    print() # Cleanliness line
    instance = ZenConfigTests(CONFIG_PATH_1, SPEC_PATH_1)

    tables = zc.ConfigTables(instance.metaconf, instance, tabletype=AsciiTable)

    info_sec_str = tables.tabledata['info']['tablestr']
    basic_sec_str = tables.tabledata['basic']['tablestr']
    advanced_sec_str = tables.tabledata['advanced']['tablestr']

    info_sec_results = regex_test_lines(info_sec_str, INFO_SEC_REGEX)
    for entry, result in info_sec_results:
        if result is not True:
            raise ValueError(f"{entry} did not match")

    basic_sec_results = regex_test_lines(basic_sec_str, BASIC_SEC_REGEX)
    for entry, result in basic_sec_results:
        if result is not True:
            raise ValueError(f"{entry} did not match")

    advanced_sec_results = regex_test_lines(advanced_sec_str, ADVANCED_SEC_REGEX)
    for entry, result in advanced_sec_results:
        if result is not True:
            raise ValueError(f"{entry} did not match")

def test_error_tree_is_valid():
    print() # Cleanliness line
    instance = ZenConfigTests(CONFIG_PATH_1, SPEC_PATH_1)

    errortree = zc.ErrorTree(
        instance.metaconf,
        include_missing=True,
        include_valid=True
    )

    # There should be no errors (valid)
    assert errortree.valid is True

    # Check tree string as well
    tree_str = errortree.get_tree
    for line in tree_str.splitlines():
        if ': ' in line:
            assert 'Valid' in line

if __name__ == '__main__':
    pytest.main()
