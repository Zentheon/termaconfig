# zenconfig/utils.py

def preprocess_config(config_data):
    """Preprocesses configuration data by stripping quotes from values and trimming whitespace.

    Args:
        config_data (file-like object): The file-like object containing the raw configuration data.

    Returns:
        list: A list of modified lines with quotes stripped and whitespace trimmed.
    """
    modified_lines = []
    for line in config_data.read().split('\n'):
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = strip_quotes(value.strip())
            modified_line = f"{key}={value}"
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)
    return modified_lines

def get_nested_value(dictionary, keys):
    """Searches for a value in a dict using the provided list of keys as the search path.

    Returns:
         value: The value of the found key.

    Raises:
        KeyError: If the dict does not contain the provided key path.
    """
    for key in keys:
        if key not in dictionary:
            raise KeyError(f"Path {keys} not found in dictionary.")
        dictionary = dictionary.get(key)
    return dictionary

def sanitize_str(input_data):
    """Sanitizes a given input by converting it into a consistent, easy to read string.

    Args:
        input_data (str, list, dict, int, float): The data to be sanitized.
            str: Removes surrounding quotes and normalizes formatting.
            list: Sanitizes individual items and separates them with ', '
            dict: Recursively sanitizes values. Returns the dict back, _not_ a string.
            int: Converts to str
            float: Converts to str

    Returns:
        str or dict: The sanitized string representation of the input data.

    Raises:
        ValueError: If the input data is of an unsupported type.
    """
    if isinstance(input_data, str):
        # Normalizes formatting, such as escaped newline codes, ect.
        sanitized_str = input_data.encode('latin-1', 'backslashreplace').decode('unicode-escape')
        # Remove any surrounding quotes
        sanitized_str = sanitized_str.strip('"').strip("'")
        return sanitized_str
    elif isinstance(input_data, list):
        # Convert list to a string with each element separated by ', '
        return ', '.join(map(sanitize_str, input_data))
    elif isinstance(input_data, dict):
        # Recursively sanitize dictionary values
        #
        return {key: sanitize_str(value) for key, value in input_data.items()}
    elif isinstance(input_data, int) or isinstance(input_data, float):
        # Convert numbers to strings
        return str(input_data)
    else:
        raise ValueError("Unsupported data type")

def join_wrapped_list(items, entries_per_line):
    """Joins a list into a string with items separated by commas and wrapped to multiple lines."""
    if not items:
        return ""

    result = []
    for i in range(0, len(items), entries_per_line):
        line = ', '.join(map(str, items[i:i + entries_per_line]))
        result.append(line)

    return "\n".join(result)

def strip_quotes(input_string):
    """Strips leading and trailing quotes from a string if they are the same type (single or double).

    Args:
        input_string (str): The string to strip quotes from.

    Returns:
        str: The original string with outer matching quotes removed.
    """
    if input_string.startswith("'") and input_string.endswith("'"):
        return input_string[1:-1]
    elif input_string.startswith('"') and input_string.endswith('"'):
        return input_string[1:-1]
    else:
        return input_string

def strip_metakeys(input_dict, delimiter):
    """Takes an input config dict and removes keys with the delimiter in them. Use the returned spec to run validation on."""
    stripped_spec = {}
    for key, value in input_dict.items():
        if delimiter not in key:
            if isinstance(value, dict):
                new_value = strip_metakeys(value, delimiter)
                if new_value:
                    stripped_spec[key] = new_value
            else:
                stripped_spec[key] = value
    return stripped_spec

def squash_true_dicts(in_dict):
    """Recursively squashes a dictionary into a single True value if all containing keys are True. Modifies nothing otherwise."""
    all_true = True

    for key, value in in_dict.items():
        if isinstance(value, dict):
            result = squash_true_dicts(value)
            if result is not True:
                all_true = False
                break
        elif value is not True:
            all_true = False
            break

    return True if all_true else in_dict

def remove_true_keys(input_dict):
    """Recursively removes all keys from a dictionary where the value is True.

    Args:
        input_dict (dict): The dictionary to process.

    Returns:
        dict: A new dictionary with keys having values of True removed.
    """
    result = {}

    for key, value in input_dict.items():
        if isinstance(value, dict):
            cleaned_sub_dict = remove_true_keys(value)
            if cleaned_sub_dict:
                result[key] = cleaned_sub_dict
        elif value is not True:
            result[key] = value

    return result

def parse_string_values(input_str):
    """Extracts and returns a dict object from a string formatted as '{any string}(key1=value1,key2=value2,...)'.

    Args:
        input_str (str): A string containing key-value pairs separated by commas.
            The string should be in the format `{any string}(key1=value1,key2=value2,...)`.

    Returns:
        str: The first part (key) of the string before brackets.
        dict: The tuple-formatted str in dict form. Keys with no values are returned as None.

    Raises:
        ValueError: If the input string format is incorrect or if there are invalid key-value pairs.
    """
    try: index = input_str.index('(')
    except ValueError: return input_str, None

    parent_key = input_str[:index]
    # Get second half (value) of the str. Also trim off the trailing bracket
    tuple = input_str[index + 1:][:-1]

    # Handle nested tuple-like objects
    open_bracket_index = tuple.find('(')
    if open_bracket_index != -1:
        close_bracket_index = tuple.find(')', open_bracket_index + 1)
        if close_bracket_index == -1:
            raise ValueError(f"{input_str} is not valid: Opening bracket with no closer")
        sub_list = tuple[open_bracket_index + 1:close_bracket_index]
        # Temporarily swap out commas for double semicolon so the list as treated as once item
        new_sub_list = sub_list.replace(',', ';;')
        tuple = tuple.replace(sub_list, new_sub_list)

    items = tuple.split(',')
    value_dict = {}
    for idx, item in enumerate(items):
        item = strip_quotes(item.strip())

        item_parts = item.split('=')
        # Items with no values
        if len(item_parts) == 1:
            key = item_parts[0].strip()
            val = None
        # Items longer than two (key=value) are invalid
        elif len(item_parts) != 2:
            raise ValueError(f"Invalid key-value pair format: {item_parts}")
        # Regular key=value pairs
        else:
            key, val = item_parts
            key = key.strip()
            val = val.strip().strip('"').replace(';;', ',')

        value_dict[key] = val

    return parent_key, value_dict
