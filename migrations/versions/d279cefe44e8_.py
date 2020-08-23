"""empty message

Revision ID: d279cefe44e8
Revises: 7ba6577baa38
Create Date: 2020-08-23 03:07:04.273279

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd279cefe44e8'
down_revision = '7ba6577baa38'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('candidates', sa.Column('ssn', sa.String(length=10), nullable=True))

def downgrade():
    op.drop_column('candidates', 'ssn')