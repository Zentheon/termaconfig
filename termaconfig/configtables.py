# termaconfig/configtables.py

import logging as log
from copy import deepcopy

import terminaltables3 as tt3

import termaconfig as tc
import termaconfig.utils as util
from termaconfig.exceptions import TableTypeError


class ConfigTables:
    """Manages the creation and manipulation of tables based on a configuration spec.

    This class provides methods to traverse a configuration specification, process table sections,
    create tables from the data, and format them using the terminaltables3 library.

    It's designed and intended to work for ConfigObj, but will work with any similarly formatted inputs.

    Once called, you can retrieve any singular
    """

    def __init__(self, metaconf, config, **kwargs):
        # I ended up realizing that tabledata is actually iterating upon the
        # same object pointer as metaconf, which is bad.
        # Instead of refactoring logic again, deepcopy becomes a saving grace here
        tabledata = deepcopy(metaconf)

        # Verify input terminaltables class
        self.tabletype = kwargs.get("tabletype", None)
        if self.tabletype:
            if not isinstance(self.tabletype, type(tt3.AsciiTable)):
                raise TableTypeError(f"Input table class is not valid: {self.tabletype}")
        else:
            self.tabletype = tt3.SingleTable

        self.delimiter = kwargs.get("delimiter", "__")

        self.config = config

        tabledata = self._process_table_sections(tabledata, config)
        tabledata = self._create_table_rows(tabledata)
        tabledata = self._process_table_strings(tabledata, self.tabletype)

        self.tabledata = tabledata

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
        alltables = ""
        log.debug("Converting tabledata to table lines")
        for entry, details in self.tabledata.items():
            if details["tablestr"]:
                alltables += details["tablestr"] + "\n"
        if alltables != "":
            return alltables
        else:
            return None

    def _process_table_strings(self, tabledata, tabletype):
        """Creates table representations of the processed config table data using terminaltables3

        This property iterates through each entry in tabledata, checks if it contains a 'table' key,
        and if so, creates a SingleTable instance using terminaltables3. It then formats the table
        based on the presence of 'title', 'header', and other details before appending it to a string.

        Returns:
            dict: The input dict with a 'SingleTable' str in each entry.
        """
        log.debug("Converting table row lists to strings")
        for entry, details in tabledata.items():
            if not details["tablerows"]:
                tabledata[entry]["tablestr"] = None
                continue
            try:
                table_instance = tabletype(details.get("tablerows", []))
            except TypeError as e:
                raise TypeError(f"{e}. Was a correct terminaltables class passed?")

            # Header row would have already been handled if present
            if not details["header"]:
                table_instance.inner_heading_row_border = False
            if details["title"]:
                table_instance.title = details["title"]
            tabledata[entry]["tablestr"] = table_instance.table
        return tabledata

    def _get_config_section(self, entry, details, config):
        keys = entry.split(".")
        value_from_config = util.get_nested_value(config, keys)
        if not isinstance(value_from_config, dict):
            return details
        for key, value in value_from_config.items():
            details["data"][key] = {}
            details["data"][key]["value"] = value
        return details

    def _handle_type(self, tabledata, entry, details, config):
        """__type is a multi-option setting for controlling how to display all entries in the section."""
        details = (
            details.copy()
        )  # We need details to act functionally separate from the tables entry
        # __type: Handling logic
        if not details["type"]:
            return tabledata

        # Since a type would imply variable entries, we want to get all entries from the config
        # section instead of using individual keys assotated with the spec.
        details = self._get_config_section(entry, details, config)

        if not details["wrap"]:
            details["wrap"] = 6
        else:
            try:
                details["wrap"] = int(details["wrap"])
            except ValueError as e:
                raise ValueError(f"{e}. Is {self.delimiter}wrap in {entry} an integer?")

        tabledata[entry]["data"] = {}
        if details["type"] == "variable":
            tabledata[entry]["data"] = details["data"]
            return tabledata
        elif details["type"] == "list_values":
            values = [
                str(data.get("value", ""))
                for key, data in details["data"].items()
                if "value" in data
            ]
            tabledata[entry]["data"][entry] = {
                "title": details.get("title", None),
                "value": util.join_wrapped_list(values, details["wrap"]),
                "note": details.get("note", None),
            }
        elif details["type"] == "list_keys":
            keys = [str(data.get("title", key)) for key, data in details["data"].items()]
            tabledata[entry]["data"][entry] = {
                "title": details.get("title", None),
                "value": ", ".join(keys),
                "note": details.get("note", None),
            }
        elif details["type"] == "list_all":
            entries = [
                f"{data.get('title', key)} ({data.get('value', '')})"
                for key, data in details["data"].items()
            ]
            tabledata[entry]["data"][entry] = {
                "title": details.get("title", None),
                "value": ", ".join(entries),
                "note": details.get("note", None),
            }
        else:
            raise ValueError(f"The specified type '{details['type']}' for '{entry}' is not valid.")

        tabledata[entry]["data"][entry] = util.fill_required_keys(
            tabledata[entry]["data"][entry], tc.REQUIRED_PARAM_KEYS
        )
        # Return section entries to None, so no nasty double lines occur
        tabledata[entry]["title"] = None
        tabledata[entry]["note"] = None

        return tabledata

    def _handle_header(self, tabledata, entry, details):
        """Processes the __header metakey

        Headers should only be shown if the header metakey exists. It is expected as a list
        representing the table row.
        """
        if not details["header"]:
            return tabledata

        header_value = details["header"]
        try:
            header_list = [util.sanitize_str(item.strip()) for item in header_value.split(",")]
            log.debug(f"Found a valid header list: {header_list}")
        except Exception as e:
            log.error(f"Failed to parse header value for {entry}: {e}")
            header_list = []

        if len(header_list) > 0:
            header_dict = {
                "__header__": {
                    "title": header_list[0],
                    "value": header_list[1] if len(header_list) > 1 else "",
                }
            }
            header_dict["__header__"] = util.fill_required_keys(
                header_dict["__header__"], tc.REQUIRED_PARAM_KEYS
            )
            if len(header_list) > 2:
                header_dict["__header__"]["note"] = header_list[2]
            # Positionally unpack dicts so __header__ is at the top
            tabledata[entry]["data"] = {**header_dict, **tabledata[entry]["data"]}
        return tabledata

    def _handle_parent(self, tabledata, entry, details):
        # __parent: Table merging logic.
        # Should be the last thing processed so we're not trying to access a deleted dict
        if details["parent"]:
            parent_section = details["parent"]
            if parent_section in tabledata:
                if details["spacer"]:
                    spacer = util.fill_required_keys({}, tc.REQUIRED_PARAM_KEYS)
                    tabledata[parent_section]["data"][f"{entry}{self.delimiter}spacer"] = spacer
                if details["title"]:
                    title = {"value": "", "title": details["title"]}
                    title = util.fill_required_keys(title, tc.REQUIRED_PARAM_KEYS)
                    tabledata[parent_section]["data"][f"{entry}{self.delimiter}title"] = title

                tabledata[parent_section]["data"].update(details["data"])
                del tabledata[entry]
            else:
                raise ValueError(f"Parent setting: {parent_section} not found for option: {entry}")
        return tabledata

    def _process_table_sections(self, tabledata, config):
        """Master function handling all the options set for config sections"""
        for entry, details in list(tabledata.items()):
            try:
                # __ignore: We set the str value to a proper bool here, if it wasn't already.
                if str(tabledata[entry]["ignore"]).lower() == "true":
                    tabledata[entry]["ignore"] = True
                    continue
                else:
                    tabledata[entry]["ignore"] = False

                # __toggle should be taken as a full dot-notated path to another config option.
                if details["toggle"]:
                    toggle_parts = details["toggle"].split(".")
                    section_path = ".".join(toggle_parts[:-1])
                    setting_key = toggle_parts[-1]
                    # Since we can't just have
                    if section_path in tabledata and setting_key in tabledata[section_path]["data"]:
                        # The config parser should have already set up datatypes, but str is checked to be safe.
                        if (
                            str(tabledata[section_path]["data"][setting_key]["value"]).lower()
                            == "false"
                        ):
                            tabledata[entry]["ignore"] = True
                            continue

                tabledata = self._handle_type(tabledata, entry, details, config)
                tabledata = self._handle_header(tabledata, entry, details)
                tabledata = self._handle_parent(tabledata, entry, details)
            except Exception:
                raise
        return tabledata

    def _create_table_rows(self, tabledata):
        """Handles the options set in individual settings and adds the `table` lists to `tables[entry]`"""
        for entry in tabledata:
            tabledata[entry]["tablerows"] = []
            try:
                if tabledata[entry]["ignore"]:
                    continue
                if "data" not in tabledata[entry]:
                    continue

                keys_to_remove = []
                for key, data in tabledata[entry]["data"].items():
                    if data["ignore"]:
                        keys_to_remove.append(key)
                for key in keys_to_remove:
                    del tabledata[entry]["data"][key]
                # Add the table row data
                for key, data in tabledata[entry]["data"].items():
                    # The value entry check *should* be redundant
                    if "value" not in tabledata[entry]["data"][key]:
                        continue
                    if data["title"]:
                        table_row = [tabledata[entry]["data"][key]["title"], data["value"]]
                    else:
                        table_row = [key, data["value"]]

                    if data["note"]:
                        table_row.append(data["note"])

                    tabledata[entry]["tablerows"].append(table_row)
            except Exception:
                raise
        return tabledata
