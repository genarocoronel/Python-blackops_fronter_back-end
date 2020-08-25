"""empty message

Revision ID: aed2f9c121c9
Revises: d279cefe44e8
Create Date: 2020-08-25 18:29:58.139297

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'aed2f9c121c9'
down_revision = 'd279cefe44e8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('clients', sa.Column('best_time', sa.String(length=5), nullable=True))
    op.add_column('clients', sa.Column('loc_time_zone', sa.String(length=3), nullable=True))


def downgrade():
    op.drop_column('clients', 'loc_time_zone')
    op.drop_column('clients', 'best_time')