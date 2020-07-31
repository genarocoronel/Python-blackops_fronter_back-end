"""Pinnacle Phone nums

Revision ID: e76856d91c94
Revises: 6c337407d8fe
Create Date: 2020-07-07 21:26:25.347972

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e76856d91c94'
down_revision = '6c337407d8fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pinnacle_phone_numbers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('number', sa.String(length=20), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('number')
    )
    op.add_column('campaigns', sa.Column('pinnacle_phone_num_id', sa.Integer(), nullable=True))
    op.create_foreign_key('campaigns_pinnacle_phone_num_id_fkey', 'campaigns', 'pinnacle_phone_numbers', ['pinnacle_phone_num_id'], ['id'])
    op.drop_column('campaigns', 'pinnacle_phone_no')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('campaigns', sa.Column('pinnacle_phone_no', sa.VARCHAR(length=100), autoincrement=False, nullable=True))
    op.drop_constraint('campaigns_pinnacle_phone_num_id_fkey', 'campaigns', type_='foreignkey')
    op.drop_column('campaigns', 'pinnacle_phone_num_id')
    op.drop_table('pinnacle_phone_numbers')
    # ### end Alembic commands ###