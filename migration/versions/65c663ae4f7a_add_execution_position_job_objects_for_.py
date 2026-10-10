"""Add execution_position job objects for separation of work creation and execution.

Revision ID: 65c663ae4f7a
Revises: 555ec6da45b4
Create Date: 2026-10-05 11:31:06.284497

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision= '65c663ae4f7a'
down_revision = '555ec6da45b4'
branch_labels = None
depends_on = None

def upgrade():
    """Upgrade schema."""
    op.add_column(
        'job',
        sa.Column(
            'execution_position',
            sa.Integer(),
            nullable=True,
            comment='execution ordering among matching jobs'
        ),
    )

    # Update new execution_position from existing job objects
    op.execute(
        sa.text('''
        UPDATE job
        SET execution_position = job_template.execution_position
        FROM job_template
        WHERE job.job_template_id = job_template.id
        ''')
    )

    # New column not-nullable
    op.alter_column(
        'job',
        'execution_position',
        existing_type=sa.Integer(),
        nullable=False,
    )

    # Update comment on ofp_file
    op.alter_column(
        'ofp_file',
        'archive_path',
        existing_type=sa.VARCHAR(),
        comment=
            'Path file was moved to for archiving. Field remains null until'
            ' work for the file is finished.',
        existing_comment='Path file was moved to for archiving.',
        existing_nullable=True,
    )

def downgrade():
    """Downgrade schema."""
    op.alter_column(
        'ofp_file',
        'archive_path',
        existing_type=sa.VARCHAR(),
        comment='Path file was moved to for archiving.',
        existing_comment=
            'Path file was moved to for archiving. Field remains null until'
            ' work for the file is finished.',
        existing_nullable=True)
    op.drop_column('job', 'execution_position')
