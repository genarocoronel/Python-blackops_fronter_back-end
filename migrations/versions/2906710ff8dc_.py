"""empty message

Revision ID: 2906710ff8dc
Revises: cefc86f7839b
Create Date: 2020-06-04 12:15:14.229180

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2906710ff8dc'
down_revision = 'cefc86f7839b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('clients', sa.Column('sales_rep_id', sa.Integer(), nullable=True))
    op.create_foreign_key('clientst_sales_rep_id_fkey', 'clients', 'users', ['sales_rep_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('clientst_sales_rep_id_fkey', 'clients', type_='foreignkey')
    op.drop_column('clients', 'sales_rep_id')
    # ### end Alembic commands ###
