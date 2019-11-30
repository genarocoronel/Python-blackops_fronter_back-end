"""empty message

Revision ID: c57e199ff06c
Revises: 314d4f195106
Create Date: 2019-11-29 22:25:20.346273

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from app.main.seed.contact_number_types import seed_contact_number_types

revision = 'c57e199ff06c'
down_revision = '1bba6d989a01'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    contact_number_types = op.create_table('contact_number_types',
                                           sa.Column('id', sa.Integer(), nullable=False),
                                           sa.Column('inserted_on', sa.DateTime(), nullable=False),
                                           sa.Column('name', sa.String(length=50), nullable=False),
                                           sa.Column('description', sa.Text(), nullable=True),
                                           sa.PrimaryKeyConstraint('id'),
                                           sa.UniqueConstraint('name')
                                           )
    op.create_table('contact_numbers',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('contact_number_type_id', sa.Integer(), nullable=True),
                    sa.Column('phone_number', sa.String(length=20), nullable=False),
                    sa.Column('preferred', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['contact_number_type_id'], ['contact_number_types.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('candidate_contact_number',
                    sa.Column('candidate_id', sa.Integer(), nullable=False),
                    sa.Column('contact_number_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['contact_number_id'], ['contact_numbers.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'contact_number_id')
                    )
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.create_unique_constraint('email', ['email'])

    op.bulk_insert(contact_number_types, seed_contact_number_types())

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('credit_report_accounts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')

    op.drop_table('candidate_contact_number')
    op.drop_table('contact_numbers')
    op.drop_table('contact_number_types')
    # ### end Alembic commands ###
