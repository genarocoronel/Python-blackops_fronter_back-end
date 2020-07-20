"""Candidate Best Time

Revision ID: 4c626890b350
Revises: bedaece16d8a
Create Date: 2020-07-20 18:20:30.042518

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4c626890b350'
down_revision = 'bedaece16d8a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('candidates', sa.Column('best_time', sa.String(length=5), nullable=True))
    op.add_column('candidates', sa.Column('loc_time_zone', sa.String(length=3), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    op.drop_column('candidates', 'loc_time_zone')
    op.drop_column('candidates', 'best_time')
    # ### end Alembic commands ###
