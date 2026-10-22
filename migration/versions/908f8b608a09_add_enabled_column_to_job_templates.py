"""Add enabled column to job templates

Revision ID: 908f8b608a09
Revises: 59508b92659b
Create Date: 2026-10-21 15:23:43.060272

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision= '908f8b608a09'
down_revision = '59508b92659b'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade schema."""
    op.add_column(
        'job_template',
        sa.Column(
            'is_enabled',
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

def downgrade():
    """Downgrade schema."""
    op.drop_column('job_template', 'is_enabled')
