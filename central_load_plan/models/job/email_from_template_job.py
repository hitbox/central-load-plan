import smtplib
import uuid

from email.message import EmailMessage

import sqlalchemy as sa

from flask import current_app

from central_load_plan import rendering

from .job_type import JobTypeEnum
from .polybase import Job

class EmailFromTemplateJob(Job):

    __tablename__ = 'email_from_template_job'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.EMAIL_FROM_TEMPLATE.name,
    }

    from_email_id = sa.Column(sa.Uuid, sa.ForeignKey('email.id'))

    from_email = sa.orm.relationship('Email')

    send_tos = sa.orm.relationship(
        'SendTo',
        back_populates = 'email_from_template_job',
    )

    template_name = sa.Column(sa.String, nullable=False)

    subject = sa.Column(
        sa.String,
        nullable=False,
        comment = 'Format string given scraped OFP data for email subject',
    )

    id = sa.Column(
        sa.Uuid,
        sa.ForeignKey('job.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    def do_work(self):
        config = current_app.config

        smtp_host = config.get('SMTP_HOST')
        if not smtp_host:
            raise RuntimeError("SMTP_HOST not configured")

        smtp_port = config.get('SMTP_PORT', 0)

        # Build OFP data
        ofp_data = self.ofp_file.as_dict_with_crew()

        # Resolve addresses
        from_addr = self.from_email.address.format(**ofp_data)

        to_addresses = [
            send_to.email.address.format(**ofp_data)
            for send_to in self.send_tos
        ]

        # Render subject + body
        subject = self.subject.format(**ofp_data)
        body = rendering.render(self.template_name, ofp_data)

        # Build message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addresses)

        # You could switch to add_alternative for HTML later
        msg.set_content(body)

        # Send
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.send_message(msg)
