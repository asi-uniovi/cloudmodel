"""Internal utility functions"""


def repr_attr(obj, attr, show_field_names=True):
    if show_field_names:
        return f"{attr}={repr(getattr(obj, attr))}"
    else:
        return repr(getattr(obj, attr))


def simplified_repr(*fields, show_field_names=True):
    """This decorator modifies the default __repr__ of namedtuples to show
    only the class name and the selected fields as parameters, instead
    of all fields
    """

    def decorator(cls):
        args = [f for f in fields if f in cls.__dataclass_fields__]
        cls.__repr__ = (
            lambda self: f"{cls.__name__}({', '.join(repr_attr(self, f, show_field_names) for f in args)})"
        )
        return cls

    return decorator


class MyTuple(tuple[float, ...]):
    """Custom version of tuple which is represented as Tuple[n] in output, instead of (x,x,x,x,x....)"""

    def __repr__(self):
        return f"Tuple[{len(self)}]"
