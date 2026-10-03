import re


def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)

    cleaned_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()

        if len(sentence) > 10:
            cleaned_sentences.append(sentence)

    return cleaned_sentences