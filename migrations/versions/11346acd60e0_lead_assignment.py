"""Lead Assignment

Revision ID: 11346acd60e0
Revises: c86a4ee4f59d
Create Date: 2020-05-02 19:50:48.839825

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '11346acd60e0'
down_revision = 'c86a4ee4f59d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user_lead_assignments',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'client_id')
    )

def downgrade():  
    op.drop_table('user_lead_assignments')
