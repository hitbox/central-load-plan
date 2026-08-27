import uuid

import sqlalchemy as sa

from markupsafe import Markup

from central_load_plan.extension import db

class Email(db.Model):

    __tablename__ = 'email'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    address = sa.Column(sa.String, unique=True, nullable=False)

    display_name = sa.Column(sa.String, nullable=True)

    send_tos = sa.orm.relationship(
        'SendTo',
        back_populates = 'email',
    )

    send_to_templates = sa.orm.relationship(
        'SendToTemplate',
        back_populates = 'email',
    )

    def address_for_ofp_data(self, ofp_data):
        """
        Get email address from data scraped from ofp files.
        """
        return self.address.format(**ofp_data)

    @property
    def as_html(self):
        return Markup(f'<address>{ self.address }</address>')
