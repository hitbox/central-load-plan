"""Add original_path, mtime composite index for existence check

Revision ID: 59508b92659b
Revises: 6d290561e4ce
Create Date: 2026-10-12 01:50:43.894317

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision= '59508b92659b'
down_revision = '6d290561e4ce'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade schema."""
    op.create_index(
        'ix_ofp_file_original_path_mtime',
        'ofp_file',
        ['original_path', 'mtime'],
        unique=False,
    )

def downgrade():
    """Downgrade schema."""
    op.drop_index(
        'ix_ofp_file_original_path_mtime',
        table_name='ofp_file',
    )
