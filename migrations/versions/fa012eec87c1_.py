"""empty message

Revision ID: fa012eec87c1
Revises: a992a1c8d1ed
Create Date: 2019-11-18 20:43:20.633317

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa012eec87c1'
down_revision = 'a992a1c8d1ed'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('docusign_signature',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('envelope_id', sa.String(length=200), nullable=False),
    sa.Column('status', sa.Enum('SENT', 'CREATED', 'DELIVERED', 'COMPLETED', 'DECLINED', 'SIGNED', 'VOIDED', name='signaturestatus'), nullable=False),
    sa.Column('created_date', sa.DateTime(), nullable=True),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('template_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.ForeignKeyConstraint(['template_id'], ['docusign_template.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('envelope_id')
    )
    op.create_unique_constraint(None, 'docusign_template', ['ds_key'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'docusign_template', type_='unique')
    op.drop_table('docusign_signature')
    # ### end Alembic commands ###