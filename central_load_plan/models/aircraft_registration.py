import uuid

import sqlalchemy as sa

from central_load_plan.extension import db

class AircraftRegistration(db.Model):
    """
    Aircraft registration code.
    """

    __tablename__ = 'aircraft_registration'

    id = sa.Column(sa.Uuid, primary_key=True, default=uuid.uuid4)

    registration_number = sa.Column(
        sa.String,
        unique = True,
        nullable = False,
    )
