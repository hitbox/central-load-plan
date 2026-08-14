"""
Custom Jinja template filters.
"""

def combine(*args):
    """
    Jinja filter to combine zero or more dicts into one.
    """
    result = {}
    for arg in args:
        if isinstance(arg, dict):
            result.update(arg)
        else:
            raise ValueError(f'Invalid type {type(arg)}')
    return result


def init_app(app):
    """
    Add template filters to flask app.
    """
    app.jinja_env.filters['combine'] = combine
