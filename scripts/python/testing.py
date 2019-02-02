#
# Use `fuzzer`, `ddmin` and the given `test`
# to find the minimal length string that causes
# `test` to return 'FAIL'.
#
import random


def fuzzer():
    # Strings up to 1024 characters long
    string_length = int(random.random() * 1024)
    out = ""
    for i in range(0, string_length):
        out += chr(int(random.random() * 96 + 32))  # filled with ASCII 32..128
    return out


def ddmin(s, test):
    n = 2     # Initial granularity
    while len(s) >= 2:
        start = 0
        subset_length = len(s) / n
        some_complement_is_failing = False

        while start < len(s):
            complement = s[:start] + s[start + subset_length:]

            if test(complement) == "FAIL":
                s = complement
                n = max(n - 1, 2)
                some_complement_is_failing = True
                break

            start += subset_length

        if not some_complement_is_failing:
            if n == len(s):
                break
            n = min(n * 2, len(s))
    return s


def test():
    return None


if __name__ == "__main__":
    test()
