"""Portal Messaging

Revision ID: 83c425803511
Revises: 6201629f612a
Create Date: 2020-05-18 03:24:16.340806

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '83c425803511'
down_revision = '6201629f612a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('portal_messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('public_id', sa.String(length=100), nullable=True),
    sa.Column('inserted_on', sa.DateTime(), nullable=True),
    sa.Column('content', sa.String(length=918), nullable=True),
    sa.Column('direction', sa.String(length=20), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('author_name', sa.String(length=50), nullable=True),
    sa.Column('is_viewed', sa.Boolean(), nullable=True),
    sa.Column('portal_user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['portal_user_id'], ['portal_users.id'], name='fk_portal_messages_portal_users_id'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('portal_messages')
    # ### end Alembic commands ###