"""empty message

Revision ID: e5abaf6732a1
Revises: f93ac9a4b808
Create Date: 2020-09-23 13:23:08.680631

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e5abaf6732a1'
down_revision = 'f93ac9a4b808'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('candidates', sa.Column('best_time_pos', sa.String(length=6), nullable=True))


def downgrade():
    op.drop_column('candidates', 'best_time_pos')