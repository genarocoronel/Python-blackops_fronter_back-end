"""empty message

Revision ID: 81ec762a312a
Revises: 1b607187235a
Create Date: 2020-08-11 21:56:21.440779

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '81ec762a312a'
down_revision = '1b607187235a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('debt_disputes', sa.Column('collector_id', sa.Integer(), nullable=False))
    op.create_foreign_key('debt_disputes_collector_id_fkey', 'debt_disputes', 'debt_collectors', ['collector_id'], ['id'])
    op.drop_column('debt_disputes', 'sp_date')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('debt_disputes', sa.Column('sp_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.drop_constraint('debt_disputes_collector_id_fkey', 'debt_disputes', type_='foreignkey')
    op.drop_column('debt_disputes', 'collector_id')
    # ### end Alembic commands ###
