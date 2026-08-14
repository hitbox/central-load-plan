from flask_wtf import FlaskForm
from markupsafe import Markup
from markupsafe import escape

def render_field_picocss(field, **kwargs):
    html = [
        f'<label for="{escape(field.id)}">{escape(field.label.text)}',
    ]

    if field.flags.required:
        html.append('<span aria-hidden="true">*</span>')

    html.append('</label>')

    kwargs.setdefault('id', field.id)
    kwargs.setdefault('aria_invalid', 'true' if field.errors else 'false')
    kwargs.setdefault(
        'aria_describedby',
        f'{field.id}-helper' if field.errors else None,
    )

    html.append(str(field(**kwargs)))

    if field.errors:
        html.append(f'<ul id="{escape(field.id)}-helper" class="errors">')
        for error in field.errors:
            html.append(f'<li>{escape(error)}</li>')
        html.append('</ul>')

    return Markup(''.join(html))

def render_field_list(field, **kwargs):
    html = ['<ul>']
    for subfield in field:
        if subfield.type == 'CSRFField':
            continue
        html.append(str(subfield(**kwargs)))
    html.append('</ul>')
    return Markup(''.join(html))

def init_app(app):
    app.jinja_env.globals['render_field_picocss'] = render_field_picocss
