# zenconfig/utils.py

def get_nested_value(dictionary, keys):
    """Searches for a value in a dict using the provided list of keys as the search path.

    Returns:
         value: The value of the found key.

    Raises:
        KeyError: If the dict does not contain the provided key path.
    """
    for key in keys:
        if key not in dictionary:
            raise KeyError(f"Key ({key}) not found in dictionary.")
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

def strip_metakeys(input_dict):
    """Takes an input config dict and removes keys with @ in them. Use the returned spec to run validation on."""
    stripped_spec = {}
    for key, value in input_dict.items():
        if "@" not in key:
            if isinstance(value, dict):
                new_value = strip_metakeys(value)
                if new_value:
                    stripped_spec[key] = new_value
            else:
                stripped_spec[key] = value
    return stripped_spec

def squash_bool_dict_tree(in_dict):
    """Recursively squashes a dictionary into a single True value if all containing keys are True."""
    all_values_true = True
    for key, value in in_dict.items():
        if isinstance(value, dict):
            result = squash_bool_dict_tree(value)
            if not result:
                all_values_true = False
            else:
                in_dict[key] = result
        elif isinstance(value, bool):
            all_values_true &= value
        else:
            all_values_true = False

    return all_values_true or in_dict

def get_values_from_string(input_str):
    """Extracts and returns a dict object from a string formatted as '{any string}(key1=value1,key2=value2,...)'.

    Args:
        input_str (str): A string containing key-value pairs separated by commas.
            The string should be in the format `{any string}(key1=value1,key2=value2,...)`.

    Returns:
        dict: The tuple-formatted str in dict form. Keys with no values are returned as None.

    Raises:
        ValueError: If the input string format is incorrect or if there are invalid key-value pairs.
    """

    parts = input_str.split('(')
    if len(parts) != 2:
        raise ValueError(f"Invalid input format: {input_str}")

    key_and_values_part = parts[1].split(')')
    if len(key_and_values_part) != 2:
        raise ValueError(f"Invalid input format: {key_and_values_part}")

    key_and_values_str = key_and_values_part[0]
    value_dict = {}
    for item in key_and_values_str.split(','):
        item_parts = item.split('=')
        if len(item_parts) == 1:
            k = item_parts[0].strip()
            v = None
        elif len(item_parts) != 2:
            raise ValueError(f"Invalid key-value pair format: {item_parts}")
        else:
            k, v = item_parts
            k = k.strip()
            v = v.strip().strip('"')

        value_dict[k] = v

    return value_dict

# flatten_errors from ConfigObj.
# Type checkers are happier with both lists being explicitly initialized
def flatten_errors(config, result, levels=[], results=[]):
    """
    An example function that will turn a nested dictionary of results (as returned by ``ConfigObj.validate``) into a flat list.

    ``config`` is the ConfigObj instance being checked, ``results`` is the results dictionary returned by ``validate``.

    (This is a recursive function, so you shouldn't use the ``levels`` or ``results`` arguments - they are used by the function.)

    Returns:
        list: A list of keys that failed. Each member of the list is a tuple:

            (list of sections..., key, result)

    If ``validate`` was called with ``preserve_errors=False`` (the default), then ``result`` will always be ``False``.

    *list of sections* is a flattened list of sections that the key was found in.

    If the section was missing (or a section was expected and a scalar provided - or vice-versa) then `key` will be ``None``.

    If the value (or section) was missing then `result` will be ``False``.

    If ``validate`` was called with ``preserve_errors=True`` and a value was present, but failed the check, then `result` will be the exception object returned. You can use this as a string that describes the failure.

    For example *The value "3" is of the wrong type*.
    """

    if result == True:
        return sorted(results)
    if result == False or isinstance(result, Exception):
        results.append((levels[:], None, result))
        if levels:
            levels.pop()
        return sorted(results)
    for (key, val) in list(result.items()):
        if val == True:
            continue
        if isinstance(config.get(key), dict):
            # Go down one level
            levels.append(key)
            flatten_errors(config[key], val, levels, results)
            continue
        results.append((levels[:], key, val))

    # Go up one level
    if levels:
        levels.pop()

    return sorted(results)
