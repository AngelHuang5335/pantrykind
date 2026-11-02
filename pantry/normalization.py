import unicodedata


def food_key(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())
