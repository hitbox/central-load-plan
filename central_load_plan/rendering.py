import textwrap

from jinja2 import FileSystemLoader
from jinja2 import Environment

env = Environment(
    loader = FileSystemLoader('central_load_plan/output_templates'),
)

def sliding_match(substr, text):
    """
    Slide along `text` looking for the best match of `substr`.
    """
    best = 0
    best_index = None
    i = 0
    while True:
        look = text[i:i+len(substr)]
        nmatch = sum(c1 == c2 for c1, c2 in zip(look, substr))
        if nmatch > best:
            best = nmatch
            best_index = i
        i += 1
        if i + len(substr) >= len(text):
            break
    return best_index

def clean_remove(substr, text):
    """
    match some `substr` in `text`, removing everything from the beginning of
    `text` to the first space after `substr`.
    """
    # TODO: replace runs of whitespace with one space?
    i = sliding_match(substr, text)
    if i:
        # find first space after substr
        i = text.find(' ', i+len(substr))
        text = text[i:].strip()
    return text

def fullv1(status, **textwrap_options):
    """
    De-duplicate the item number from the description. Look for an place on a
    newline, the text "Expiration Date:" and everything after it.
    """
    description = clean_remove(status['item'], status['description'])

    items = description.rpartition('Expiration Date:')
    before, expdate, after = items
    if before and expdate and after:
        before = '\n'.join(textwrap.wrap(before, **textwrap_options))
        after = '\n'.join(textwrap.wrap(expdate + after, **textwrap_options))

        if 'subsequent_indent' in textwrap_options:
            subsequent_indent = textwrap_options['subsequent_indent']
        else:
            subsequent_indent = ''

        description = before + '\n' + subsequent_indent + after

    return description

def render(template, data):
    """
    Render email body text from airline specific template.
    """
    template = env.get_template(template)
    context = dict(
        textwrap = textwrap,
        clean_remove = clean_remove,
        fullv1 = fullv1,
    )
    context.update(data)
    return template.render(**context)
