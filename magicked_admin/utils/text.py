import math
import re

def millify(n):
    millnames = ['', 'K', 'M', 'B', 'T']
        
    n = float(n)
    millidx = max(0,
                  min(len(millnames)-1,
                      int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

    return '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])


def trim_string(input_str, length):
    return (input_str[:length-2] + '..') if len(input_str) > length \
        else input_str

# Attempts to pad a string in non-monospace fonts. Assumes "ilt " are all half-width.
def visual_ljust(string, length):
    return string.ljust(len(string) + 2 * (length - len(string)) + len(re.findall("[ilt ]", string)))

def visual_rjust(string, length):
    return string.rjust(len(string) + 2 * (length - len(string)) + len(re.findall("[ilt ]", string)))

def str_to_bool(s):
    if s in ['True', 'true', '1']:
        return True
    elif s in ['False', 'false', '0']:
        return False
    else:
        raise ValueError
