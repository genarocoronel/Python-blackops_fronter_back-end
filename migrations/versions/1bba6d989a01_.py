"""empty message

Revision ID: 1bba6d989a01
Revises: 314d4f195106
Create Date: 2019-11-28 11:06:49.163314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1bba6d989a01'
down_revision = '314d4f195106'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('registered_fraud_insurance', sa.Boolean(), nullable=False, default=False))


def downgrade():
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.drop_column('registered_fraud_insurance')
