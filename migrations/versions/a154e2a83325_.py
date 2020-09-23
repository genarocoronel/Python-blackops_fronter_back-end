"""empty message

Revision ID: a154e2a83325
Revises: 0fe357e9a2ce
Create Date: 2020-09-22 17:09:06.961053

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a154e2a83325'
down_revision = '0fe357e9a2ce'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('candidates', sa.Column('best_time_pos', sa.String(length=6), nullable=True))


def downgrade():
    op.drop_column('candidates', 'best_time_pos')
