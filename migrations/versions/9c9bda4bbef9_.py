"""empty message

Revision ID: 9c9bda4bbef9
Revises: f439b7bcd64f
Create Date: 2020-02-21 07:17:53.642373

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9c9bda4bbef9'
down_revision = 'f439b7bcd64f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bank_account_validation_status',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category', sa.Enum('passed', 'failed', name='statuscategory'), nullable=True),
    sa.Column('code', sa.String(length=10), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('bank_account_validation_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('bav_status_id', sa.Integer(), nullable=True),
    sa.Column('account_number', sa.String(length=100), nullable=False),
    sa.Column('routing_number', sa.String(length=9), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['bav_status_id'], ['bank_account_validation_status.id'], ),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('bank_accounts', sa.Column('address', sa.String(length=100), nullable=True))
    op.add_column('bank_accounts', sa.Column('bank_name', sa.String(length=125), nullable=False))
    op.add_column('bank_accounts', sa.Column('bav_status_id', sa.Integer(), nullable=True))
    op.add_column('bank_accounts', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('bank_accounts', sa.Column('owner_name', sa.String(length=100), nullable=True))
    op.add_column('bank_accounts', sa.Column('ssn', sa.String(length=9), nullable=True))
    op.add_column('bank_accounts', sa.Column('zip', sa.String(length=10), nullable=True))
    op.create_foreign_key(None, 'bank_accounts', 'bank_account_validation_status', ['bav_status_id'], ['id'])
    op.drop_column('bank_accounts', 'name')
    op.alter_column('client_monthly_expenses', 'candidate_id', new_column_name='client_id', existing_type=sa.Integer)
    op.drop_constraint('client_monthly_expenses_candidate_id_fkey', 'client_monthly_expenses', type_='foreignkey')
    op.create_foreign_key('client_monthly_expenses_client_id_fkey', 'client_monthly_expenses', 'clients', ['client_id'], ['id'])
    # ### end Alembic commands ###
    op.execute("COMMIT")
    op.execute("ALTER TYPE clienttype ADD VALUE 'coclient'")


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('client_monthly_expenses', 'client_id', new_column_name='candidate_id', existing_type=sa.Integer)
    op.drop_constraint('client_monthly_expenses_client_id_fkey', 'client_monthly_expenses', type_='foreignkey')
    op.create_foreign_key('client_monthly_expenses_candidate_id_fkey', 'client_monthly_expenses', 'clients', ['candidate_id'], ['id'])
    op.add_column('bank_accounts', sa.Column('name', sa.VARCHAR(length=125), autoincrement=False, nullable=False))
    op.drop_constraint('bank_accounts_client_id_fkey', 'bank_accounts', type_='foreignkey')
    op.drop_column('bank_accounts', 'zip')
    op.drop_column('bank_accounts', 'ssn')
    op.drop_column('bank_accounts', 'owner_name')
    op.drop_column('bank_accounts', 'email')
    op.drop_column('bank_accounts', 'bav_status_id')
    op.drop_column('bank_accounts', 'bank_name')
    op.drop_column('bank_accounts', 'address')
    op.drop_table('bank_account_validation_history')
    op.drop_table('bank_account_validation_status')
    statuscategory = postgresql.ENUM('passed', 'failed',  name='statuscategory')
    statuscategory.drop(op.get_bind())
    # ### end Alembic commands ###
