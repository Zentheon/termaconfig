# zenconfig/configtables.py

import logging as log
import terminaltables3 as tt3

from zenconfig.exceptions import TableTypeError
from zenconfig.utils import get_nested_value, sanitize_str, join_wrapped_list

class ConfigTables:
    """Manages the creation and manipulation of tables based on a configuration spec.

    This class provides methods to traverse a configuration specification, process table sections,
    create tables from the data, and format them using the terminaltables3 library.

    It's designed and intended to work for ConfigObj, but will work with any similarly formatted inputs.

    Once called, you can retrieve any singular
    """
    def __init__(self, config, spec, **kwargs):
        # Verify input terminaltables class
        self.tabletype = kwargs.get('tabletype', None)
        if self.tabletype:
            if not isinstance(self.tabletype, type(tt3.AsciiTable)):
                raise TableTypeError(f"Input table class is not valid: {self.tabletype}")
        else: self.tabletype = tt3.SingleTable

        self.delimiter = kwargs.get('delimiter', '__')

        self.config = config
        self.spec = spec
        self.tabledata = {}
        tables = self.tabledata

        tables = self._traverse_configspec([], config, spec, tables)
        tables = self._process_table_sections(tables, config)
        tables = self._create_table_rows(tables)
        tables = self._process_table_strings(tables, self.tabletype)

    @property
    def all_tables(self):
        """Returns a string containing all tables created from configspec parameters.

        This property iterates through each entry in tabledata, checks if it contains a 'tablestr' key,
        and if so, creates a table instance using the passed terminaltables3 class. It then formats
        the table based on the presence of 'title', 'header', and other details before appending
        it to a string.

        Returns:
            str or None: A long multi-line string containing all the table strings from tabledata[entries]['tablestr'] if any, otherwise None.
        """
        alltables = ''
        log.debug("Converting tabledata to table lines")
        for entry, details in self.tabledata.items():
            if details['tablestr']:
                alltables += details['tablestr'] + '\n'
        if alltables != '':
            return alltables
        else: return None

    def _process_table_strings(self, tables, tabletype):
        """Creates table representations of the processed config table data using terminaltables3

        This property iterates through each entry in tabledata, checks if it contains a 'table' key,
        and if so, creates a SingleTable instance using terminaltables3. It then formats the table
        based on the presence of 'title', 'header', and other details before appending it to a string.

        Returns:
            dict: The input dict with a 'SingleTable' str in each entry.
        """
        log.debug("Converting table row lists to strings")
        for entry, details in tables.items():
            if not details['tablerows']:
                tables[entry]['tablestr'] = None
                continue
            try:
                table_instance = tabletype(details.get('tablerows', []))
            except TypeError as e:
                raise TypeError(f"{e}. Was a correct terminaltables class passed?")

            # Header row would have already been handled if present
            if not 'header' in details:
                table_instance.inner_heading_row_border = False
            if 'title' in details:
                table_instance.title = details['title']
            tables[entry]['tablestr'] = table_instance.table
        return tables

    def _get_config_section(self, entry, details, config):
        keys = entry.split('.')
        value_from_config = get_nested_value(config, keys)
        if not isinstance(value_from_config, dict):
            return details
        for key, value in value_from_config.items():
            details['data'][key] = {}
            details['data'][key]['value'] = value
        return details

    def _handle_type(self, tabledata, entry, details, config):
        """__type is a multi-option setting for controlling how to display all entries in the section."""
        details = details.copy() # We need details to act functionally separate from the tables entry
        # __type: Handling logic
        if not 'type' in details:
            return tabledata

        # Since a type would imply variable entries, we want to get all entries from the config
        # section instead of using individual keys assotated with the spec.
        details = self._get_config_section(entry, details, config)

        if not 'wrap' in details:
            details['wrap'] = 6
        else:
            try: details['wrap'] = int(details['wrap'])
            except ValueError as e:
                raise ValueError(f"{e}. Is {self.delimiter}wrap in {entry} an integer?")

        tabledata[entry]['data'] = {}
        if details['type'] == 'variable':
            tabledata[entry]['data'] = details['data']
            return tabledata
        elif details['type'] == 'list_values':
            values = [str(data.get('value', '')) for key, data
                in details['data'].items() if 'value' in data]
            tabledata[entry]['data'][entry] = {
                'title': details.get('title', ''),
                'value': join_wrapped_list(values, details['wrap']),
                'note': details.get('note', '')
            }
        elif details['type'] == 'list_keys':
            keys = [str(data.get('title', key)) for key, data in details['data'].items()]
            tabledata[entry]['data'][entry] = {
                'title': details.get('title', ''),
                'value': ', '.join(keys),
                'note': details.get('note', '')
            }
        elif details['type'] == 'list_all':
            entries = [f"{data.get('title', key)} ({data.get('value', '')})" for key, data
                in details['data'].items()]
            tabledata[entry]['data'][entry] = {
                'title': details.get('title', ''),
                'value': ', '.join(entries),
                'note': details.get('note', '')
            }
        else:
            raise ValueError(f"The specified type '{details['type']}' for '{entry}' is not valid.")

        if 'title' in tabledata[entry]:
            del tabledata[entry]['title']
        if 'note' in tabledata[entry]:
            del tabledata[entry]['note']

        return tabledata

    def _handle_header(self, tables, entry, details):
        """Processes the __header metakey

        Headers should only be shown if the header metakey exists. It is expected as a list
        representing the table row.
        """
        if 'header' in details:
            header_value = details['header']
            try:
                header_list = [sanitize_str(item.strip()) for item in header_value.split(',')]
                log.debug(f"Found a valid header list: {header_list}")
            except Exception as e:
                log.error(f"Failed to parse header value for {entry}: {e}")
                header_list = []

            if len(header_list) > 0:
                header_dict = {'__header__': {
                    'title': header_list[0],
                    'value': header_list[1] if len(header_list) > 1 else '',
                }}
                if len(header_list) > 2:
                    header_dict['__header__']['note'] = header_list[2]
                # Positionally unpack dicts so __header__ is at the top
                tables[entry]['data'] = {**header_dict, **tables[entry]['data']}
        return tables

    def _handle_parent(self, tables, entry, details):
        # __parent: Table merging logic.
        # Should be the last thing processed so we're not trying to access a deleted dict
        if 'parent' in details:
            parent_section = details['parent']
            if parent_section in tables:
                if 'spacer' in details:
                    tables[parent_section]['data'][f'{entry}{self.delimiter}spacer'] = {'value': '', 'title': ''}
                if 'title' in details:
                    tables[parent_section]['data'][f'{entry}{self.delimiter}title'] = {'value': '', 'title': details['title']}
                tables[parent_section]['data'].update(details['data'])
                del tables[entry]
            else:
                raise ValueError(f"Parent setting: {parent_section} not found for option: {entry}")
        return tables

    def _process_table_sections(self, tables, config):
        """Master function handling all the options set for config sections"""
        for entry, details in list(tables.items()):
            try:
                # __ignore: We set the str value to a proper bool here, if it wasn't already.
                if 'ignore' in tables[entry] and str(tables[entry]['ignore']).lower() == 'true':
                    tables[entry]['ignore'] = True
                    continue
                else:
                    tables[entry]['ignore'] = False

                # __toggle should be taken as a full dot-notated path to another config option.
                if 'toggle' in details:
                    toggle_parts = details['toggle'].split('.')
                    section_path = '.'.join(toggle_parts[:-1])
                    setting_key = toggle_parts[-1]
                    # Since we can't just have
                    if section_path in tables and setting_key in tables[section_path]['data']:
                        # The config parser should have already set up datatypes, but str is checked to be safe.
                        if str(tables[section_path]['data'][setting_key]['value']).lower() == 'false':
                            tables[entry]['ignore'] = True
                            continue

                tables = self._handle_type(tables, entry, details, config)
                tables = self._handle_header(tables, entry, details)
                tables = self._handle_parent(tables, entry, details)
            except Exception:
                raise
        return tables

    def _create_table_rows(self, tabledata):
        """Handles the options set in individual settings and adds the `table` lists to `tables[entry]`"""
        for entry in tabledata:
            tabledata[entry]['tablerows'] = []
            try:
                if tabledata[entry]['ignore']:
                    continue
                if 'data' not in tabledata[entry]:
                    continue

                keys_to_remove = []
                for key, data in tabledata[entry]['data'].items():
                    if data.get('ignore', False):
                        keys_to_remove.append(key)
                for key in keys_to_remove:
                    del tabledata[entry]['data'][key]
                # Add the table row data
                for key, data in tabledata[entry]['data'].items():
                    # The value entry check *should* be redundant
                    if 'value' not in tabledata[entry]['data'][key]:
                        continue
                    if 'title' in data:
                        table_row = [tabledata[entry]['data'][key]['title'], data['value']]
                    else:
                        table_row = [key, data['value']]

                    # Check for note key and append to table row if present
                    if 'note' in data:
                        table_row.append(data['note'])

                    tabledata[entry]['tablerows'].append(table_row)
            except Exception:
                raise
        return tabledata

    def _traverse_configspec(self, keys, config, opperating_dict, tabledata):
        """
        Recursively searches in a provided config specification and an assotiated, validated config.
        A `tables` dict is created containing parsed metakey information along with values from the input config.
        """
        # Validate inputs
        if not isinstance(opperating_dict, dict):
            raise TypeError(f"Expected loaded specification dict, not '{opperating_dict}'")
        if not isinstance(config, dict):
            raise TypeError(f"Expected loaded config dict, not '{config}'")

        key_path = '.'.join(keys)
        if key_path and key_path not in tabledata:
            tabledata[key_path] = {}
            tabledata[key_path]['data'] = {}
        for key, value in opperating_dict.items():
            value = sanitize_str(value)
            current_keys = keys + [key]
            parent_key = key.split(self.delimiter)[0]
            meta_key = key.split(self.delimiter)[-1]
            value_from_config = None
            if parent_key:
                try:
                    value_from_config = sanitize_str(get_nested_value(config, keys + [parent_key]))
                # The provided config should already be validated and defaults filled.
                # If an entry doesn't match up, there's probably something wrong.
                except KeyError:
                    raise KeyError(f"Path: {'.'.join(keys + [parent_key])} was not found in config. Is there a typo in the config spec?")

            if self.delimiter in key:
                # Section configs start with delimiter
                if key.startswith(self.delimiter):
                    tabledata[key_path][meta_key] = value
                # Per-setting values get added to a respective nested dict
                else:
                    # Initialize target setting dict if needed
                    if not parent_key in tabledata[key_path]['data']:
                        tabledata[key_path]['data'][parent_key] = {}

                    tabledata[key_path]['data'][parent_key][meta_key] = value
            elif isinstance(value, dict):
                # Recursively traverse nested sections
                tabledata = self._traverse_configspec(current_keys, config, value, tabledata)
            else:
                if not key in tabledata[key_path]['data']:
                    tabledata[key_path]['data'][key] = {}
                tabledata[key_path]['data'][key]['value'] = value_from_config

        return tabledata
