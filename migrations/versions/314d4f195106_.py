"""empty message

Revision ID: 314d4f195106
Revises: 0b1ff683301f
Create Date: 2019-11-27 13:42:51.085133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '314d4f195106'
down_revision = '0b1ff683301f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=30), nullable=True))
        sa.UniqueConstraint('public_id')


def downgrade():
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.drop_column('email')
