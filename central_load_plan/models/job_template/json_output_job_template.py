import uuid

import sqlalchemy as sa

from markupsafe import Markup

from ..job import JobTypeEnum
from ..job import JSONOutputJob

from .polybase import JobTemplate

class JSONOutputJobTemplate(JobTemplate):

    __job_class__ = JSONOutputJob

    __tablename__ = 'json_output_template_job_template'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.JSON_FILE.name,
    }

    __python_defaults__ = {
        'execution_position': 30,
        'min_size': 1, # no empty files
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    output_path = sa.Column(sa.String, nullable=False)

    def html_preview(self, ofp_file):
        from central_load_plan.schema import OperationalFlightPlanSchema

        ofp_data = ofp_file.as_dict_with_crew()

        html = ['<div>']
        html.append('<p>Output Path</p>')
        output_path = self.output_path.format(**ofp_data)

        html.append(f'<p>{ output_path }</p>')

        schema = OperationalFlightPlanSchema()
        content = schema.dump(ofp_data)

        html.append('<p>Content</p>')
        html.append(f'<pre class="value">{ content }</pre>')

        html.append('</div>')
        return Markup(''.join(html))

    def make_job(self, ofp_file):
        return self.__job_class__(
            ofp_file = ofp_file,
            name = self.name,
            output_path = self.output_path,
        )

