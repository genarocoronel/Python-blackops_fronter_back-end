"""Portal Callsheet

Revision ID: f046787c1b38
Revises: 83c425803511
Create Date: 2020-05-18 06:09:43.359082

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f046787c1b38'
down_revision = '83c425803511'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('portal_callsheet',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('public_id', sa.String(length=100), nullable=True),
    sa.Column('inserted_on', sa.DateTime(), nullable=True),
    sa.Column('updated_on', sa.DateTime(), nullable=True),
    sa.Column('is_orig_creditor', sa.Boolean(), nullable=True),
    sa.Column('is_hardship_call', sa.Boolean(), nullable=True),
    sa.Column('debt_name', sa.String(length=75), nullable=True),
    sa.Column('creditor_name', sa.String(length=75), nullable=True),
    sa.Column('collector_name', sa.String(length=75), nullable=True),
    sa.Column('received_from_phone_number', sa.String(length=20), nullable=True),
    sa.Column('received_on_phone_type', sa.String(length=10), nullable=True),
    sa.Column('notes', sa.String(length=918), nullable=True),
    sa.Column('is_file_attached', sa.Boolean(), nullable=True),
    sa.Column('portal_user_id', sa.Integer(), nullable=True),
    sa.Column('docproc_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['docproc_id'], ['docproc.id'], name='fk_portal_callsheets_docproc_id'),
    sa.ForeignKeyConstraint(['portal_user_id'], ['portal_users.id'], name='fk_portal_callsheets_portal_users_id'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('portal_callsheet')
    # ### end Alembic commands ###