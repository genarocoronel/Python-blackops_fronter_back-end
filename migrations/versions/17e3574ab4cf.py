"""expand email field size

Revision ID: 17e3574ab4cf
Revises: c0d9a442072b
Create Date: 2020-01-20 18:25:17.970530

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '17e3574ab4cf'
down_revision = 'c0d9a442072b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.alter_column('email',
                              existing_type=sa.VARCHAR(length=255),
                              type_=sa.String(length=255),
                              existing_nullable=True)


def downgrade():
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.alter_column('email',
                              existing_type=sa.VARCHAR(length=255),
                              type_=sa.String(length=255),
                              existing_nullable=True)
