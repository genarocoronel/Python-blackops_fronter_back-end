"""Auditor

Revision ID: ddb123661445
Revises: 81ec762a312a
Create Date: 2020-08-20 19:59:55.635245

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ddb123661445'
down_revision = '81ec762a312a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('audit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('public_id', sa.String(length=100), nullable=True),
    sa.Column('inserted_on', sa.DateTime(), nullable=True),
    sa.Column('auditable', sa.String(length=25), nullable=True),
    sa.Column('auditable_subject_pubid', sa.String(length=100), nullable=True),
    sa.Column('action', sa.String(length=100), nullable=True),
    sa.Column('requestor_username', sa.String(length=20), nullable=True),
    sa.Column('message', sa.String(length=140), nullable=True),
    sa.Column('is_internal', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('audit')
    # ### end Alembic commands ###
