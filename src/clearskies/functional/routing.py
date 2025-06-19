import re


def match_route(expected_route, incoming_route, allow_partial=False) -> tuple[bool, dict[str, str]]:
    """
    Check if two routes match, and returns the routing data if so.

    A partial match happens when the beginning of the incoming route matches the expected route.  It's okay for the
    incoming route to be longer because the routing system is hierarchical, so a partial match at the beginning
    can work.  e.g.:

    Expected route: `/users`
    Incoming route: `/users/orders/5`

    But note that it must fully match all route segments, so this is never a match:

    Expected route: `/user`
    Incoming route: `/users/orders/5`
    """
    expected_route = expected_route.strip("/")
    incoming_route = incoming_route.strip("/")

    expected_parts = expected_route.split("/")
    incoming_parts = incoming_route.split("/")

    # quick check: if there are less parts in the incoming route than the expected route, then we can't possibly match
    if len(incoming_parts) < len(expected_parts):
        return (False, {})
    # ditto the opposite, if we can't do a partial match
    if len(expected_parts) < len(incoming_parts) and not allow_partial:
        return (False, {})

    # if we got this far then we will do a more complete match, so let's find any routing parameters
    routing_data = {}
    routing_parameters = extract_url_parameter_name_map(expected_route)
    # we want it backwards
    routing_parameters_by_index = {value: key for (key, value) in routing_parameters.items()}
    for index in range(len(expected_parts)):
        if index in routing_parameters_by_index:
            if not incoming_parts[index]:
                return (False, {})
            routing_data[routing_parameters_by_index[index]] = incoming_parts[index]
        else:
            if expected_parts[index] != incoming_parts[index]:
                return (False, {})

    return (True, routing_data)


def extract_url_parameter_name_map(url: str) -> dict[str, int]:
    """
    Create a map to help match URLs with routing parameters.

    Routing parameters are either brace enclosed or start with colons:

    ```python
    print(
        routing.extract_url_parameter_name_map("my/path/{some_parameter}/:other_parameter/more/paths")
    )
    # prints {"some_parameter": 2, "other_parameter": 3}
    ```

    Note that leading and trailing slashes are stripped, so "/my/path/{id}" and "my/path/{id}" give identical
    parameter maps: `{"id": 2}`
    """
    parameter_name_map = {}
    path_parts = url.strip("/").split("/")
    for index, part in enumerate(path_parts):
        if not part:
            continue
        if part[0] == ":":
            match = re.match("^:(\\w[\\w\\d_]{0,})$", part)
        else:
            if part[0] != "{":
                continue
            if part[-1] != "}":
                raise ValueError(
                    f"Invalid route configuration for URL '{url}': section '{part}'"
                    + " starts with a '{' but does not end with one"
                )
            match = re.match("^{(\\w[\\w\\d_]{0,})\\}$", part)
        if not match:
            raise ValueError(
                f"Invalid route configuration for URL '{url}', section '{part}': resource identifiers must start with a letter and contain only letters, numbers, and underscores"
            )
        parameter_name = match.group(1)
        if parameter_name in parameter_name_map:
            raise ValueError(
                f"Invalid route configuration for URL '{url}', a URL path named '{parameter_name}' appeared more than once."
            )
        parameter_name_map[parameter_name] = index
    return parameter_name_map
