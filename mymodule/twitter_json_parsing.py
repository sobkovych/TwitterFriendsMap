"""Parse json files."""
import json
import re


def search_for_key(final_key: str, tree: dict, space: list = []):
    """Search all data for a key.

    :param final_key: the key
    :param tree: the data
    :param space: found values
    :return: all found values
    """
    if isinstance(tree, dict) and final_key in tree.keys():
        space.append(tree[final_key])
        tree.pop(final_key)

    if isinstance(tree, dict):
        for key in tree:
            search_for_key(final_key, tree[key])

    elif isinstance(tree, list):
        for item in tree:
            search_for_key(final_key, item)

    else:
        return None

    return space


def check_response(prompt: str, to_return: bool = False,
                   field: (tuple, None) = ({"yes", "y", "true", "t", "1"},
                                           {"no", "n", "false", "f", "0"}),
                   expression: str = None,
                   max_len: int = None,
                   min_len: int = None) -> (bool, str):
    """Check responce by params.

    :param prompt: input message
    :param to_return: whether to return responce
    :param field: values to avoid/look for
    :param expression: regular expr check
    :param max_len: max len check
    :param min_len: min len check
    :return: bool or value
    """
    if field:
        affirm = field[0] if field[0] else None
        negat = field[1] if field[1] else None
    else:
        affirm = negat = None

    while True:
        resp = input(prompt).lower()
        ret_value = resp if to_return else True

        if affirm and resp in affirm:
            return ret_value
        if negat and resp in negat:
            return False

        if expression:
            print(re.compile(expression))
        if expression and re.fullmatch(expression, resp):
            return ret_value

        if min_len and len(resp) >= min_len:
            return ret_value
        if max_len and len(resp) <= max_len:
            return ret_value
        else:
            print("The response is incorrect, try again!")


def get_step_by_step(obj):
    """Parse obj step by step.

    :param obj: list, dict or other
    :return: found value or None
    """
    space = [(obj, "JSON")]

    unsure = check_response("Ask to come back at every step?\n")

    while True:
        if isinstance(obj, dict):
            print("This obj is a dict. These are the available keys:")
            fill_len = len(max(obj.keys(), key=len)) + 10
            for i, key in enumerate(obj):
                if i % 2 == 0:
                    row = "{}.){}".format(i+1, key)
                    row = row.ljust(fill_len, " ")
                else:
                    row = "{}.){}\n".format(i+1, key)
                print(row, end='')
            key = check_response("\nChose your key by name: ",
                                 True, field=(obj, None))
            obj = obj[key]

        elif isinstance(obj, list):
            print("This obj is a list.")
            last_key = len(obj)-1
            key = check_response(
                "Choose an index from 0 to {}: ".format(last_key),
                to_return=True,
                field=({str(i) for i in range(last_key+1)}, None)
            )
            obj = obj[int(key)]

        else:
            print("Your final obj is:  {}.".format(obj))
            if check_response("Return:  {}  (y/n)?\n".format(obj)):
                return obj
            elif check_response("Come back to any step?\n"):
                for i, step in enumerate(space):
                    print("Step {}: {}".format(i+1, step[1]))
                l_space = len(space)
                step = check_response("Which step to come back to "
                                      "within range "
                                      "[1, {}]?\n".format(l_space),
                                      to_return=True,
                                      field=(
                                          {str(i+1) for i in range(l_space)},
                                          None
                                      ))
                step = int(step)
                obj = space[step-1][0]
                del space[step:]
                continue
            else:
                print("Returning None...")
                return None

        space.append((obj, key))
        if unsure:
            while (len(space) > 1 and
                   check_response("Come back to previous step(y/n)?\n")):
                space.pop()
                obj = space[-1][0]
                print("Now at step {}: {}".format(len(space), space[-1][1]))


def main(get: str, store: str = None, mode: str = "step"):
    """Find the leaf(user input) in the tree(method - user input).

    (from 'kved.json' file)
    :param store: where to store the result tree.
    """
    with open(get, encoding="utf-8") as f:
        tree = json.load(f)

    if check_response("Analyse step by step(y/n)?\n"):
        print(get_step_by_step(tree))

    if check_response("Search for key(y/n)?\n"):
        user_key = input("Enter your key: ")
        print(search_for_key(user_key, tree=tree))

    if store:
        with open(store, mode="w+", encoding="utf-8") as outfile:
            json.dump(tree, outfile, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main("form.json")
