import os


def insert_before_keyword(s, keyword, new_string):
    """
    Inserts a string before a keyword in a string.

    Args:
        s (str): The original string.
        keyword (str): The keyword to search for in the string.
        new_string (str): The string to insert before the keyword.

    Returns:
        str: The modified string.
    """
    # Find the index of the keyword in the string
    index = s.find(keyword)

    # If the keyword is not found, return the original string
    if index == -1:
        return s

    # Insert the new string before the keyword
    modified_string = s[:index] + new_string + s[index:]

    return modified_string


def get_filename_sonarhash(outfile):
    filename_sonarhash = os.path.splitext(outfile)[0] + ".sonar_hash"
    return filename_sonarhash
