import json

from markupsafe import Markup
from wtforms import Field
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.widgets import TextArea
from wtforms.widgets import TextInput
from wtforms.widgets import html_params

class AddFieldListEntry(SubmitField):
    """
    A SubmitField that adds a new entry to a FieldList via JavaScript.
    """

    def __init__(self, label=None, fieldlist_id=None, **kwargs):
        """
        fieldlist_id: HTML id of the container of the FieldList entries
        """
        super().__init__(label, **kwargs)
        self.fieldlist_id = fieldlist_id

    def __call__(self, **kwargs):
        # Render normal button
        html = f'<button type="button" id="{self.id}">{self.label.text}</button>'

        # Add JS to clone empty entry
        html += f"""
        <script>
        document.getElementById("{self.id}").addEventListener('click', function() {{
            const container = document.getElementById("{self.fieldlist_id}");
            const index = container.children.length;

            // Find the empty form template
            const template = document.getElementById("{self.fieldlist_id}-template");
            let clone = template.cloneNode(true);
            clone.style.display = 'block';
            clone.removeAttribute('id');

            // Update all input/select names and ids
            clone.querySelectorAll('input, select, textarea').forEach(function(el) {{
                el.name = el.name.replace(/__prefix__/, index);
                el.id = el.id.replace(/__prefix__/, index);
                el.value = '';
            }});

            container.appendChild(clone);
        }});
        </script>
        """
        return Markup(html)



class JSONField(Field):
    """
    A WTForms field that handles JSON input.
    Converts the input string into a Python dictionary/list.
    """

    widget = TextInput()

    def _value(self):
        if self.data:
            return json.dumps(self.data)
        return ''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = json.loads(valuelist[0])
            except ValueError as e:
                raise ValidationError(f'Invalid JSON {e}')
        else:
            self.data = None
