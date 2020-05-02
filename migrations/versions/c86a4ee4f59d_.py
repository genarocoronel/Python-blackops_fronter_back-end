"""empty message

Revision ID: c86a4ee4f59d
Revises: 3e295f6460be
Create Date: 2020-04-25 20:19:30.087448

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c86a4ee4f59d'
down_revision = '3e295f6460be'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('fax_communications', sa.Column('public_id', sa.String(length=100), nullable=True))
    op.create_unique_constraint('fax_communications_public_id_key', 'fax_communications', ['public_id'])
    op.add_column('voice_communications', sa.Column('public_id', sa.String(length=100), nullable=True))
    op.create_unique_constraint('voice_communications_public_id_key', 'voice_communications', ['public_id'])

    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("UPDATE fax_communications SET public_id = uuid_generate_v4() WHERE public_id is NULL")
    op.execute("UPDATE voice_communications SET public_id = uuid_generate_v4() WHERE public_id is NULL")

    op.alter_column('fax_communications', 'public_id', nullable=False)
    op.alter_column('voice_communications', 'public_id', nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('voice_communications_public_id_key', 'voice_communications', type_='unique')
    op.drop_column('voice_communications', 'public_id')
    op.drop_constraint('fax_communications_public_id_key', 'fax_communications', type_='unique')
    op.drop_column('fax_communications', 'public_id')
    # ### end Alembic commands ###
