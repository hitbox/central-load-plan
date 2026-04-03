from markupsafe import Markup
from wtforms.widgets import html_params

class NestedFormWidget:
    """
    Widget to render a FormField (nested form) or FieldList(FormField(...))
    recursively like other fields.
    """
    def __call__(self, field, **kwargs):
        html = []

        # If FieldList of forms
        if hasattr(field, 'entries'):
            for i, subfield in enumerate(field.entries):
                html.append(f'<div id="{field.id}-{i}">')
                html.append('<script>// Hello!</script>')
                html.append(f'<h4>{field.label.text} #{i+1}</h4>')
                # Recursively render all fields of the subform except submit buttons
                submit_buttons = [f for f in subfield.form if f.type.endswith('SubmitField')]
                for f in subfield.form:
                    if f not in submit_buttons:
                        html.append(f'<div>{f.label}{f()}</div>')
                if submit_buttons:
                    html.append('<div class="buttons">')
                    for button in submit_buttons:
                        html.append(str(button))
                html.append('</div>')
        # Single FormField
        elif hasattr(field, 'form'):
            html.append(f'<div id="{field.id}">')
            for f in field.form:
                if not f.type.endswith('SubmitField'):
                    html.append(f'<div>{f.label}{f()}</div>')
            html.append('</div>')
        else:
            # Fallback to default rendering
            html.append(f'<div>{field.label}{field()}</div>')

        return Markup(''.join(html))
