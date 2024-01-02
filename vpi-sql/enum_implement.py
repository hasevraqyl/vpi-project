from enum import Enum


class DiscordStatusCode(Enum):
    all_clear = 0
    no_elem = 1
    invalid_elem = 2
    unknown = 3
    no_table = 4
