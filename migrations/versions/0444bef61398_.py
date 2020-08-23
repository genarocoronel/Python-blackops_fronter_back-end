"""empty message

Revision ID: 0444bef61398
Revises: a01c59e9fff8
Create Date: 2020-08-23 02:01:33.460160

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0444bef61398'
down_revision = 'a01c59e9fff8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('candidates', sa.Column('ssn', sa.String(length=10), nullable=True))

def downgrade():
    op.drop_column('candidates', 'ssn')