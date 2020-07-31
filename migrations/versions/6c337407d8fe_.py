"""EDMS report status

Revision ID: 6c337407d8fe
Revises: 6b57068135b3
Create Date: 2020-07-01 21:19:53.788306

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6c337407d8fe'
down_revision = '6b57068135b3'
branch_labels = None
depends_on = None

options  = ('Scheduled', 'Processed', 'Settled', 'Failed')
des_type = sa.Enum(*options, name='debteftstatus')

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('debt_payment_schedule', 'status', existing_type=sa.Enum(), type_=sa.String(length=24))
    des_type.drop(op.get_bind())
    op.add_column('debt_payment_contract', sa.Column('bank_fee', sa.Float(), nullable=True))
    op.add_column('debt_payment_contract', sa.Column('credit_monitoring_fee', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('debt_payment_contract', 'credit_monitoring_fee')
    op.drop_column('debt_payment_contract', 'bank_fee')
    des_type.create(op.get_bind())
    op.execute('ALTER TABLE debt_payment_schedule ALTER COLUMN status TYPE debteftstatus'
               ' USING status::text::debteftstatus')
    # ### end Alembic commands ###