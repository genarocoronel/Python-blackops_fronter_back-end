"""empty message

Revision ID: 0094869a6471
Revises: f439b7bcd64f
Create Date: 2020-02-17 17:57:43.506759

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0094869a6471'
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
    with op.batch_alter_table('bank_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('address', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('bank_name', sa.String(length=125), nullable=False))
        batch_op.add_column(sa.Column('bav_status_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('owner_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('ssn', sa.String(length=9), nullable=True))
        batch_op.add_column(sa.Column('zip', sa.String(length=10), nullable=True))
        batch_op.create_foreign_key('bank_account_validation_status_unique_id', 'bank_account_validation_status', ['bav_status_id'], ['id'])
        batch_op.drop_column('name')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bank_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=125), nullable=False))
        batch_op.drop_constraint('bank_account_validation_status_unique_id', type_='foreignkey')
        batch_op.drop_column('zip')
        batch_op.drop_column('ssn')
        batch_op.drop_column('owner_name')
        batch_op.drop_column('email')
        batch_op.drop_column('bav_status_id')
        batch_op.drop_column('bank_name')
        batch_op.drop_column('address')

    op.drop_table('bank_account_validation_history')
    op.drop_table('bank_account_validation_status')
    # ### end Alembic commands ###
