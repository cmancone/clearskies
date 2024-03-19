import re
import datetime


def camel_case_to_snake_case(string: str) -> str:
    """
    Converts a title/camel case string (MyString|myString) to snake case (my_string)
    """
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)).lower()


def camel_case_to_title_case(string):
    return camel_case_to_words.title()


def camel_case_to_words(string):
    string = re.sub("(.)([A-Z][a-z]+)", r"\1 \2", string)
    string = re.sub("([a-z0-9])([A-Z])", r"\1 \2", string).lower()
    return string


def title_case_to_snake_case(string: str) -> str:
    """
    Converts a title case string (MyString) to snake case (my_string)
    """
    return camel_case_to_snake_case(string)


def title_case_to_camel_case(string: str) -> str:
    if len(string) == 0:
        return string
    if len(string) == 1:
        return string.lower()
    return string[0].lower() + string[1:]


def snake_case_to_title_case(string: str) -> str:
    """
    Converts a snake case string (my_string) to title case (MyString)

    Note this is sometimes ambiguous.  Consider:

    TitleCase -> snake_case  -> TitleCase
    MyDbThing -> my_db_thing -> MyDbThing
    MyDBThing -> my_db_thing -> MyDbThing
    """
    words = string.lower().split("_")
    return "".join([x.title() for x in words])


def snake_case_to_camel_case(string: str) -> str:
    """
    Converts a snake case string (my_string) to camel case (myString)

    Note this is sometimes ambiguous.  Consider:

    camelCase -> snake_case  -> camelCase
    myDbThing -> my_db_thing -> myDbThing
    myDBThing -> my_db_thing -> myDbThing
    """
    words = string.lower().split("_")
    return words[0] + "".join([x.title() for x in words[1:]])


casings = ["camelCase", "snake_case", "TitleCase"]
casing_swap_map = {
    "camelCase": {
        "camelCase": str,
        "snake_case": camel_case_to_snake_case,
        "TitleCase": camel_case_to_title_case,
    },
    "snake_case": {
        "camelCase": snake_case_to_camel_case,
        "snake_case": str,
        "TitleCase": snake_case_to_title_case,
    },
    "TitleCase": {
        "camelCase": title_case_to_camel_case,
        "snake_case": title_case_to_snake_case,
        "TitleCase": str,
    },
}


def swap_casing(string: str, from_casing: str, to_casing: str) -> str:
    if from_casing not in casings:
        raise ValueError(f"Invalid casing '{from_casing}'.  Must be one of '" + "', ".join(casings) + "'")
    if to_casing not in casings:
        raise ValueError(f"Invalid casing '{to_casing}'.  Must be one of '" + "', ".join(casings) + "'")
    return casing_swap_map[from_casing][to_casing](string)


def make_plural(singular: str):
    if singular[-1] == "y":
        return singular[:-1] + "ies"
    if singular[-1] == "s":
        return singular + "es"
    return f"{singular}s"


def datetime_to_iso(value):
    if not isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        return value
    return value.isoformat()
