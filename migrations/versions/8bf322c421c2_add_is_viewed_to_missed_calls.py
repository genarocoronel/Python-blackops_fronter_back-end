"""add is_viewed to missed calls

Revision ID: 8bf322c421c2
Revises: 9a39c01a9f0e
Create Date: 2020-10-04 18:45:59.974929

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bf322c421c2'
down_revision = '9a39c01a9f0e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('voice_call_events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_viewed', sa.Boolean(), nullable=True, default=False))


def downgrade():
    with op.batch_alter_table('voice_call_events', schema=None) as batch_op:
        batch_op.drop_column('is_viewed')
