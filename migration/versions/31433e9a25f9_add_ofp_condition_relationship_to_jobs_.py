"""Add ofp_condition relationship to jobs, remove name field from jobs

Revision ID: 31433e9a25f9
Revises: 
Create Date: 2026-08-17 13:46:49.267171

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision= '31433e9a25f9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade schema.
    """
    # Add JobTemplate relationship to Job classes.
    # Nullable to fill first.
    op.add_column(
        'job',
        sa.Column(
            'job_template_id',
            sa.Uuid(),
            nullable = True,
            comment = 'FK to the job template that created this job',
        )
    )

    # Update job_template_id by matching JobTemplate.job_type_name on existing
    op.execute(
        sa.text("""
            UPDATE job
            SET job_template_id = job_template.id
            FROM job_template
            WHERE job.job_type_name = job_template.job_type_name
        """)
    )

    # Make sure every existing Job found a template.
    connection = op.get_bind()
    unmatched = connection.execute(
        sa.text("""
            SELECT count(*)
            FROM job
            WHERE job_template_id IS NULL
        """)
    ).scalar_one()

    if unmatched:
        raise RuntimeError(
            f'{unmatched} existing job(s) could not be matched to a JobTemplate'
        )

    # Set nullable=False on job_template_id
    op.alter_column('job', 'job_template_id', nullable=False)

    # Link to the Job template will give us the condition, don't need it on Job.
    op.drop_constraint(op.f('job_ofp_condition_id_fkey'), 'job', type_='foreignkey')
    op.create_foreign_key(None, 'job', 'job_template', ['job_template_id'], ['id'])
    op.drop_column('job', 'ofp_condition_id')
    # Remove name from Job class, it's already defined on the template.
    op.drop_column('job', 'name')

def downgrade():
    """
    Downgrade schema.
    """
    op.add_column('job', sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.add_column('job', sa.Column('ofp_condition_id', sa.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'job', type_='foreignkey')
    op.create_foreign_key(op.f('job_ofp_condition_id_fkey'), 'job', 'ofp_condition', ['ofp_condition_id'], ['id'])
    op.drop_column('job', 'job_template_id')
