import re


def camel_case_to_snake_case(string: str) -> str:
    """
    Converts a title/camel case string (MyString|myString) to snake case (my_string)
    """
    return re.sub(
        '([a-z0-9])([A-Z])', r'\1_\2',
        re.sub('(.)([A-Z][a-z]+)', r'\1_\2', string)
    ).lower()

def snake_case_to_title_case(string: str) -> str:
    """
    Converts a snake case string (my_string) to title case (MyString)

    Note this is sometimes ambiguous.  Consider:

    TitleCase -> snake_case  -> TitleCase
    MyDbThing -> my_db_thing -> MyDbThing
    MyDBThing -> my_db_thing -> MyDbThing
    """
    words = string.lower().split('_')
    return ''.join([x.title() for x in words])

def snake_case_to_camel_case(string: str) -> str:
    """
    Converts a snake case string (my_string) to camel case (myString)

    Note this is sometimes ambiguous.  Consider:

    camelCase -> snake_case  -> camelCase
    myDbThing -> my_db_thing -> myDbThing
    myDBThing -> my_db_thing -> myDbThing
    """
    words = string.lower().split('_')
    return words[0] + ''.join([x.title() for x in words[1:]])
