"""empty message

Revision ID: 1b607187235a
Revises: 26bbb568a3e4
Create Date: 2020-08-09 21:06:10.360691

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b607187235a'
down_revision = '26bbb568a3e4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('debt_disputes', sa.Column('created_date', sa.DateTime(), nullable=False))
    op.add_column('debt_disputes', sa.Column('fd_noir_expired_date', sa.DateTime(), nullable=True))
    op.add_column('debt_disputes', sa.Column('fd_non_response_expired_date', sa.DateTime(), nullable=True))
    op.add_column('debt_disputes', sa.Column('is_active', sa.Boolean(), nullable=True))
    op.add_column('debt_disputes', sa.Column('noir2_date', sa.DateTime(), nullable=True))
    op.add_column('debt_disputes', sa.Column('noir_fdcpa_date', sa.DateTime(), nullable=True))
    op.add_column('debt_disputes', sa.Column('status', sa.String(length=60), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('debt_disputes', 'status')
    op.drop_column('debt_disputes', 'noir_fdcpa_date')
    op.drop_column('debt_disputes', 'noir2_date')
    op.drop_column('debt_disputes', 'is_active')
    op.drop_column('debt_disputes', 'fd_non_response_expired_date')
    op.drop_column('debt_disputes', 'fd_noir_expired_date')
    op.drop_column('debt_disputes', 'created_date')
    # ### end Alembic commands ###
