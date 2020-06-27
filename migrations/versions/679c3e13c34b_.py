"""Tickets

Revision ID: 679c3e13c34b
Revises: 68d42b11eae0
Create Date: 2020-06-24 17:54:06.280294

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '679c3e13c34b'
down_revision = '68d42b11eae0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.Column('modified_on', sa.DateTime(), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.Column('client_id', sa.Integer(), nullable=True),
    sa.Column('priority', sa.String(length=40), nullable=True),
    sa.Column('status', sa.String(length=40), nullable=True),
    sa.Column('source', sa.String(length=40), nullable=True),
    sa.Column('title', sa.String(length=120), nullable=False),
    sa.Column('desc', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='tickets_client_id_fkey'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='tickets_owner_id_fkey'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tickets')
    # ### end Alembic commands ###
