import os
import uuid

import sqlalchemy as sa

from markupsafe import Markup

from ..job import FileOutputFromTemplateJob
from ..job import JobTypeEnum

from central_load_plan import rendering

from .polybase import JobTemplate

class FileOutputFromTemplateJobTemplate(JobTemplate):

    __job_class__ = FileOutputFromTemplateJob

    __tablename__ = 'file_output_from_template_job_template'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.FILE_FROM_TEMPLATE.name,
    }

    __python_defaults__ = {
        'execution_position': 20,
        'min_size': 1, # no empty files
    }

    id = sa.Column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('job_template.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    template_name = sa.Column(sa.String, nullable=False)

    output_path = sa.Column(sa.String, nullable=False)

    def make_job(self, ofp_file):
        return self.__job_class__(
            ofp_file = ofp_file,
            name = self.name,
            template_name = self.template_name,
            output_path = self.output_path,
        )

    def html_preview(self, ofp_file):
        ofp_data = ofp_file.as_dict_with_crew()

        html = ['<div>']
        html.append('<p>Output Path</p>')
        html.append(f'<pre class="value">{os.path.normpath(ofp_file.display_path)}</pre>')

        content = rendering.render(self.template_name, ofp_data)
        html.append('<p>Content</p>')
        html.append(f'<pre class="value">{ content }</pre>')

        html.append('</div>')
        return Markup(''.join(html))
