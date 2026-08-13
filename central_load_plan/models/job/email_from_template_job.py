import smtplib
import uuid
import logging

from datetime import datetime
from email.message import EmailMessage
from html import escape

import sqlalchemy as sa

from flask import current_app

from central_load_plan import rendering

from .job_type import JobTypeEnum
from .polybase import Job

logger = logging.getLogger(__name__)

class EmailFromTemplateJob(Job):

    __tablename__ = 'email_from_template_job'

    __mapper_args__ = {
        'polymorphic_identity': JobTypeEnum.EMAIL_FROM_TEMPLATE.name,
    }

    from_email_id = sa.Column(sa.Uuid(as_uuid=True), sa.ForeignKey('email.id'))

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
        sa.Uuid(as_uuid=True),
        sa.ForeignKey('job.id'),
        primary_key = True,
        default = uuid.uuid4,
    )

    def do_work(self):
        # Wanted this to be like other extenions but that module imports the
        # base model.
        from central_load_plan.extension import smtp

        config = current_app.config

        # Build OFP data
        ofp_data = self.ofp_file.as_dict_with_crew()

        # Resolve addresses
        from_addr = self.from_email.address.format(**ofp_data)

        # The proper matching send-to addresses are created by
        # the EmailFromTemplateJobTemplate.send_tos_for_conditions method.
        to_addresses = [
            send_to.email.address.format(**ofp_data)
            for send_to in self.send_tos
        ]

        to_addresses.append('Carl.Harris@airborneglobal.com')

        # Render subject
        subject = self.subject.format(**ofp_data)

        # Create email message.
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = ', '.join(to_addresses)

        body = rendering.render(self.template_name, ofp_data, self.ofp_file)
        msg.set_content(body)

        html_body = f'<pre>{escape(body)}</pre>'
        msg.add_alternative(html_body, subtype='html')

        # Send
        smtp.send_email(msg, subject, to_addresses, body, html=html_body, sender=from_addr)
        logger.info('sent email from=%r, subject=%r, to=%r', from_addr, subject, to_addresses)
