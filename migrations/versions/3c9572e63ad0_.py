"""empty message

Revision ID: 3c9572e63ad0
Revises: 257ec1874a37
Create Date: 2020-08-06 18:55:48.006138

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3c9572e63ad0'
down_revision = '257ec1874a37'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pbx_systems',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('public_id', sa.String(length=100), nullable=True),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('updated_on', sa.DateTime(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('enabled', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    sa.UniqueConstraint('public_id')
                    )
    op.create_table('pbx_system_fax_communications',
                    sa.Column('pbx_system_id', sa.Integer(), nullable=False),
                    sa.Column('fax_communication_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['fax_communication_id'], ['fax_communications.id'], ),
                    sa.ForeignKeyConstraint(['pbx_system_id'], ['pbx_systems.id'], ),
                    sa.PrimaryKeyConstraint('pbx_system_id', 'fax_communication_id')
                    )
    op.create_table('pbx_system_voice_communications',
                    sa.Column('pbx_system_id', sa.Integer(), nullable=False),
                    sa.Column('voice_communication_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['pbx_system_id'], ['pbx_systems.id'], ),
                    sa.ForeignKeyConstraint(['voice_communication_id'], ['voice_communications.id'], ),
                    sa.PrimaryKeyConstraint('pbx_system_id', 'voice_communication_id')
                    )
    op.add_column('pbx_numbers', sa.Column('pbx_system_id', sa.Integer(), nullable=True))
    op.create_foreign_key('pbx_numbers_pbx_system_id_fkey', 'pbx_numbers', 'pbx_systems', ['pbx_system_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('pbx_numbers_pbx_system_id_fkey', 'pbx_numbers', type_='foreignkey')
    op.drop_column('pbx_numbers', 'pbx_system_id')
    op.drop_table('pbx_system_voice_communications')
    op.drop_table('pbx_system_fax_communications')
    op.drop_table('pbx_systems')
    # ### end Alembic commands ###