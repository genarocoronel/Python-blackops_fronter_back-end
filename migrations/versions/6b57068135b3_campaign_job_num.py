"""Campaign Job Num

Revision ID: 6b57068135b3
Revises: 66d8422947fd
Create Date: 2020-07-02 02:09:34.512220

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6b57068135b3'
down_revision = '66d8422947fd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('campaigns', 'job_number',
                existing_type=sa.VARCHAR(length=25),
                type_=sa.String(length=75),
                existing_nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('campaigns', 'job_number',
                existing_type=sa.VARCHAR(length=75),
                type_=sa.String(length=25),
                existing_nullable=False)
    # ### end Alembic commands ###
