"""Add job.completed_at timestamp

Revision ID: 6d290561e4ce
Revises: 65c663ae4f7a
Create Date: 2026-10-10 15:01:52.340480

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision= '6d290561e4ce'
down_revision = '65c663ae4f7a'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade schema."""
    op.add_column(
        'job',
        sa.Column(
            'completed_at',
            sa.DateTime(timezone=True),
            nullable = True,
            comment = "Job's work done at timestamp.",
        ),
    )

    confirm = 'YES'
    answer = input(f'The new `completed_at` field must be updated to a datetime to mark completed work. Stop the existing process before proceeding. Type {confirm!r} exactly to confirm you are ready.')
    if answer != confirm:
        raise ValueError(f'{answer} is not {confirm}')

    # Update the new completed_at to one second after the mtime of the
    # originally processed file.
    update_completed_at_after_mtime = sa.text(
        'UPDATE job'
        " SET completed_at = ofp_file.mtime + INTERVAL '1 second'"
        " FROM ofp_file"
        " WHERE job.ofp_file_id = ofp_file.id"
    )
    op.execute(update_completed_at_after_mtime)

def downgrade():
    """Downgrade schema."""
    op.drop_column('job', 'completed_at')
