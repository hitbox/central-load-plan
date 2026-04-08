import os
import uuid

import sqlalchemy as sa

from markupsafe import Markup
from markupsafe import escape

from ..job import EmailFromTemplateJob
from ..job import JobTypeEnum

from central_load_plan import rendering

from .polybase import JobTemplate

class EmailFromTemplateJobTemplate(JobTemplate):

    __job_class__ = EmailFromTemplateJob

    __tablename__ = 'email_from_template_job_template'

    __table_args__ = {
        'comment':
            'Template for job to send an email whose body is produced from a'
            ' jinja2 template, to a list of recipients',
    }

    __python_defaults__ = {
        'execution_position': 10,
        'min_size': 1, # no empty files
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

    send_tos = sa.orm.relationship(
        'SendToTemplate',
        back_populates = 'email_from_template_job_template',
    )

    from_email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    from_email = sa.orm.relationship('Email')

    template_name = sa.Column(sa.String, nullable=False)

    subject = sa.Column(
        sa.String,
        nullable=False,
        comment = 'Format string given scraped OFP data for email subject',
    )

    def send_tos_for_conditions(self, ofp_file):
        send_tos = []
        for send_to_template in self.send_tos:
            # Has OFPCondition and it matches or no condition.
            if (
                send_to_template.ofp_condition is None
                or
                send_to_template.ofp_condition.is_match(ofp_file)
            ):
                send_tos.append(send_to_template.make_job())
        return send_tos

    def make_job(self, ofp_file):
        return self.__job_class__(
            ofp_file = ofp_file,
            name = self.name,
            send_tos = self.send_tos_for_conditions(ofp_file),
            from_email = self.from_email,
            template_name = self.template_name,
            subject = self.subject,
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
        for send_to in self.send_tos_for_conditions(ofp_file):
            address = send_to.email.address.format(**ofp_data)
            html.append(f'<pre class="value">{ address }</pre>')

        subject = self.subject.format(**ofp_data)
        html.append('<p>Subject:</p>')
        html.append(f'<pre class="value">{ subject }</pre>')

        body = rendering.render(self.template_name, ofp_data)
        html.append('<p>Email Body:</p>')
        html.append(f'<pre class="value">{ body }</pre>')

        html.append('<p>OFP XML File Contents:</p>')
        with open(ofp_file.archive_path, 'r') as f:
            file_contents = escape(f.read())
            html.append(f'<pre class="xml value">{file_contents}</pre>')

        html.append('</div>')
        return Markup(''.join(html))
