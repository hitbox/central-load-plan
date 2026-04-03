from wtforms.widgets import ListWidget
from markupsafe import Markup

class DynamicListWidget(ListWidget):
    """
    ListWidget subclass that renders a FieldList with Add/Remove buttons.
    Uses the first subfield as a JS template.
    """

    def __call__(self, field, **kwargs):
        container_id = f"{field.id}-container"
        add_id = f"{field.id}-add"
        template_id = f"{field.id}-template"

        # Render existing fields
        fields_html = []
        for subfield in field:
            html = f'<div class="nested-field">{subfield()}'
            if subfield.errors:
                # render.html:30
                html += '<ul class="errors">'
                for error in subfield.errors:
                    html += '<li>{ error }</li>'
                html += '</ul>'
            html += '<button type="button" class="remove-btn">Remove</button>'
            html += '</div>'
            fields_html.append(html)

        # Take first field HTML as template (or empty <input> if none)
        if len(field) > 0:
            field_html = field[0]()  # Render first subfield
        else:
            field_html = '<input type="text">'

        html = f"""
<div id="{container_id}">
{"\n".join(fields_html)}
</div>
<button type="button" id="{add_id}">Add Item</button>

<template id="{template_id}">
    <div class="nested-field">
        {field_html}
        <button type="button" class="remove-btn">Remove</button>
    </div>
</template>

<script>
const container = document.getElementById("{container_id}");
const template = document.getElementById("{template_id}").content;

function reindexItems() {{
    Array.from(container.children).forEach((child, index) => {{
        child.querySelectorAll('input, select, textarea').forEach(input => {{
            input.name = input.name.replace(/-\\d+-/, `-${{index}}-`);
        }});
    }});
}}

function attachRemoveEvents() {{
    container.querySelectorAll('.remove-btn').forEach(btn => {{
        btn.onclick = () => {{
            btn.parentElement.remove();
            reindexItems();
        }};
    }});
}}

attachRemoveEvents();

document.getElementById("{add_id}").addEventListener('click', () => {{
    const clone = document.importNode(template, true);
    container.appendChild(clone);
    reindexItems();
    attachRemoveEvents();
}});
</script>
"""
        return Markup(html)
