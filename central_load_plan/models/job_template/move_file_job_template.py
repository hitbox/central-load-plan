import os
import uuid

import sqlalchemy as sa

from markupsafe import escape
from markupsafe import Markup

from ..job import JobTypeEnum
from ..job import MoveFileJob

from .polybase import JobTemplate

class MoveFileJobTemplate(JobTemplate):

    __job_class__ = MoveFileJob

    __tablename__ = 'move_file_job'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.MOVE_FILE.name,
    }

    __python_defaults__ = {
        'execution_position': 1000,
        'min_size': 0, # always move file regardless of size.
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    destination_path = sa.Column(
        sa.String,
        comment = 'Python format string produces dest. path from OFP data.'
    )

    def make_job(self, ofp_file):
        return self.__job_class__(
            ofp_file = ofp_file,
            name = self.name,
            destination_path = self.destination_path,
        )

    def html_preview(self, ofp_file):
        """
        HTML Markup for preview of the email this job template would produce.
        """
        ofp_data = ofp_file.as_dict_with_crew()

        html = ['<div>']

        html.append('<p>Name</p>')
        html.append(f'<pre>{self.name}</pre>')

        html.append('<p>Move</p>')
        html.append(f'<pre class="value">{os.path.normpath(ofp_file.display_path)}</pre>')

        html.append('<p>To</p>')
        destination_path = self.destination_path.format(**ofp_data)
        destination_path = os.path.normpath(destination_path)

        html.append(f'<pre class="value">{ escape(destination_path) }</pre>')

        html.append('</div>')
        return Markup(''.join(html))
