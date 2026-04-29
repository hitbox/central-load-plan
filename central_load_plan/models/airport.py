import uuid

import sqlalchemy as sa

from .clp_base import CLPBase

class Airport(CLPBase):
    """
    Airport station
    """

    __tablename__ = 'airport'

    id = sa.Column(
        sa.Uuid(as_uuid=True),
        primary_key = True,
        default = uuid.uuid4,
    )

    iata_code = sa.Column(
        sa.String,
        nullable = False,
        unique = True,
    )

    icao_code = sa.Column(
        sa.String,
        nullable = True,
    )
