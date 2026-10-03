from difflib import SequenceMatcher


def similarity(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio()