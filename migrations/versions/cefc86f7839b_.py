"""empty message

Revision ID: cefc86f7839b
Revises: 9b2a035631e7
Create Date: 2020-05-24 19:45:34.913129

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'cefc86f7839b'
down_revision = '9b2a035631e7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bank_account_validation_history', sa.Column('overuled', sa.Boolean(), nullable=True))
    op.add_column('bank_account_validation_history', sa.Column('overuled_by', sa.Integer(), nullable=True))
    op.create_foreign_key('bank_account_validation_history_overruled_by_fkey', 'bank_account_validation_history', 'users', ['overuled_by'], ['id'])
    op.add_column('credit_report_data', sa.Column('collector_ref_no', sa.String(length=100), nullable=True))
    op.drop_column('debt_collectors', 'account_number')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('debt_collectors', sa.Column('account_number', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.drop_column('credit_report_data', 'collector_ref_no')
    op.drop_constraint('bank_account_validation_history_overruled_by_fkey', 'bank_account_validation_history', type_='foreignkey')
    op.drop_column('bank_account_validation_history', 'overuled_by')
    op.drop_column('bank_account_validation_history', 'overuled')
    # ### end Alembic commands ###
