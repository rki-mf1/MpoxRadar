import gzip
import lzma
import os
import sys

from Bio.SeqUtils.CheckSum import seguid


def print_max_min_rule(ref):
    up = int((len(ref) * 100.3) / 100)
    low = int((len(ref) * 99.7) / 100)
    return f"Accept lenght:{low}<{len(ref)}<{up}"


def check_seq_compact(ref, qry):
    qry_size = len(qry)
    up = int((len(ref) * 100.3) / 100)
    low = int((len(ref) * 99.7) / 100)
    if low < qry_size and qry_size < up:
        return True
    else:
        return False


def hash(seq):
    """ """
    return seguid(seq)


def harmonize(seq):
    """ """
    return str(seq).strip().upper().replace("U", "T")


def open_file(fname, mode="r", compressed=False, encoding=None):
    if not os.path.isfile(fname):
        sys.exit("input error: " + fname + " does not exist.")
    if compressed == "auto":
        compressed = os.path.splitext(fname)[1][1:]
    try:
        if compressed == "gz":
            return gzip.open(fname, mode + "t", encoding=encoding)
        if compressed == "xz":
            return lzma.open(fname, mode + "t", encoding=encoding)
        else:
            return open(fname, mode, encoding=encoding)
    except Exception:
        sys.exit("input error: " + fname + " cannot be opened.")


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
