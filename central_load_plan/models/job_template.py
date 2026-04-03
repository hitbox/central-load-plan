import os
import uuid

from datetime import datetime
from enum import Enum

import sqlalchemy as sa

from markupsafe import Markup
from markupsafe import escape

from .clp_base import CLPBase
from .job_type import JobTypeEnum

from central_load_plan import rendering

class JobTemplate(CLPBase):
    """
    Named template for work to do when a condition is met against an OFPFile object.
    """

    __tablename__ = 'job_template'

    __mapper_args__ = {
        'polymorphic_on': 'job_type_name',
    }

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    name = sa.Column(sa.String, nullable=False, unique=True)

    ofp_condition_id = sa.Column(
        sa.ForeignKey('ofp_condition.id'),
        nullable = False,
    )

    ofp_condition = sa.orm.relationship(
        'OFPCondition',
    )

    job_type_name = sa.Column(sa.String)

    def make_job(self, ofp_file):
        from .job import Job
        return Job(
            ofp_file = ofp_file,
            job_type = self.job_type,
            ofp_condition = self.ofp_condition,
        )


class SendToTemplate(CLPBase):

    __tablename__ = 'send_to_template'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    send_email_job_id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('email_from_template_job_template.id'),
    )

    email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    email = sa.orm.relationship(
        'Email',
    )


class EmailFromTemplateJobTemplate(JobTemplate):

    __tablename__ = 'email_from_template_job_template'

    __table_args__ = {
        'comment':
            'Template for job to send an email whose body is produced from a'
            ' jinja2 template, to a list of recipients',
    }

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.EMAIL_FROM_TEMPLATE.name,
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    send_tos = sa.orm.relationship('SendToTemplate')

    from_email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    from_email = sa.orm.relationship('Email')

    template_name = sa.Column(sa.String, nullable=False)

    subject = sa.Column(
        sa.String,
        nullable=False,
        comment = 'Format string given scraped OFP data for email subject',
    )

    def html_preview(self, ofp_file):
        """
        HTML Markup for preview of the email this job template would produce.
        """
        ofp_data = ofp_file.as_dict_with_crew()

        html = ['<div>']

        html.append('<p>Name</p>')
        html.append(f'<pre>{self.name}</pre>')

        html.append('<p>For OFP File</p>')
        html.append(f'<pre class="value">{os.path.normpath(ofp_file.display_path)}</pre>')

        html.append('<p>From:</p>')
        html.append(f'<pre class="value">{ self.from_email.address.format(**ofp_data) }</pre>')

        html.append('<p>To:</p>')
        for send_to in self.send_tos:
            address = send_to.email.address.format(**ofp_data)
            html.append(f'<pre class="value">{ address }</pre>')

        subject = self.subject.format(**ofp_data)
        html.append('<p>Subject:</p>')
        html.append(f'<pre class="value">{ subject }</pre>')

        body = rendering.render(self.template_name, ofp_data)
        html.append('<p>Email Body:</p>')
        html.append(f'<pre class="value">{ body }</pre>')

        html.append('<p>File Contents:</p>')
        with open(ofp_file.archive_path, 'r') as f:
            file_contents = escape(f.read())
            html.append(f'<pre class="xml value">{file_contents}</pre>')

        html.append('</div>')
        return Markup(''.join(html))


class FileOutputFromTemplateJobTemplate(JobTemplate):

    __tablename__ = 'file_output_from_template_job_template'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.FILE_FROM_TEMPLATE.name,
    }

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job_template.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    template_name = sa.Column(sa.String, nullable=False)

    output_path = sa.Column(sa.String, nullable=False)

    def html_preview(self, ofp_file):
        ofp_data = ofp_file.as_dict_with_crew()

        html = ['<div>']
        html.append('<p>Output Path</p>')
        output_path = self.output_path.format(**ofp_data)
        html.append(f'<p>{ output_path }</p>')

        content = rendering.render(self.template_name, ofp_data)
        html.append('<p>Content</p>')
        html.append(f'<pre>{ content }</pre>')

        html.append('</div>')
        return Markup(''.join(html))


class JSONOutputTemplateJob(JobTemplate):

    __tablename__ = 'json_output_template_job_template'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.JSON_FILE.name,
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
        html.append(f'<pre style="white-space: pre-wrap;">{ content }</pre>')

        html.append('</div>')
        return Markup(''.join(html))
