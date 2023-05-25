import difflib

def split_hex_in_words(my_str):
    every=48
    return [str(hex(int(i/(every))*16)) + '\t' + my_str[i:i+every] + '\n' for i in range(0, len(my_str), every)]

def print_diff_with_addresses(old_bytes: bytes, new_bytes: bytes):
    old = split_hex_in_words(old_bytes.hex(" "))
    new = split_hex_in_words(new_bytes.hex(" "))
    out = list(difflib.Differ().compare(old, new))
    for line in out:
        if line.startswith('-') or line.startswith('+') or line.startswith('?'):
            print(line, end="")
    print('\n')
