"""
Analysis and visualization software

Author: Ebad Kamil <ebad.kamil@xfel.eu>
All rights reserved.
"""


def str2tuple(text, delimiter=",", handler=float):
    splitted = text[1:-1].split(delimiter)
    return handler(splitted[0]), handler(splitted[1])
