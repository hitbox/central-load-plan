import uuid

import sqlalchemy as sa

from .clp_base import CLPBase

class AircraftRegistration(CLPBase):
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
