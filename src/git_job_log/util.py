"""Utility functions for slash/separated/job/names."""
import re


def split_job(job_name: str) -> list[str]:
    """Split job_name on slashes."""
    return job_name.split("/")


def word(job_name: str, word_i: int) -> str:
    """Get the word at index word_i from job_name."""
    words = split_job(job_name)
    if word_i >= len(words):
        return ""
    return words[word_i]


def job_match(job_name: str, words: list[str]) -> bool:
    """Check if job_name matches words."""
    job_words = split_job(job_name)
    print(job_words, words)
    while job_words and len(words) <= len(job_words):
        for word_i, text in enumerate(words):
            if not re.match(text, job_words[word_i]):
                print(f"Failed on {word_i} {text} {word(job_name, word_i)}")
                break
        else:
            return True

        if job_words:
            del job_words[0]  # Try and match words further down the job_name

    return False
