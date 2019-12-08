"""empty message

Revision ID: e7049a4e4e0a
Revises: 9457beb425de
Create Date: 2019-12-07 19:32:51.014941

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from app.main.seed.expense_types import seed_expense_type_values
from app.main.seed.income_types import seed_income_types

revision = 'e7049a4e4e0a'
down_revision = '9457beb425de'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    expense_types = op.create_table('expense_types', sa.Column('id', sa.Integer(), nullable=False),
                                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                                    sa.Column('name', sa.String(length=50), nullable=False),
                                    sa.Column('display_name', sa.String(length=100), nullable=False),
                                    sa.Column('description', sa.Text(), nullable=True), sa.PrimaryKeyConstraint('id'),
                                    sa.UniqueConstraint('display_name'), sa.UniqueConstraint('name'))

    op.bulk_insert(expense_types, seed_expense_type_values())

    income_types = op.create_table('income_types', sa.Column('id', sa.Integer(), nullable=False),
                                   sa.Column('inserted_on', sa.DateTime(), nullable=False),
                                   sa.Column('name', sa.String(length=50), nullable=False),
                                   sa.Column('display_name', sa.String(length=100), nullable=False),
                                   sa.Column('description', sa.Text(), nullable=True), sa.PrimaryKeyConstraint('id'),
                                   sa.UniqueConstraint('display_name'), sa.UniqueConstraint('name'))

    op.bulk_insert(income_types, seed_income_types())

    op.create_table('income_sources',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('income_type_id', sa.Integer(), nullable=True),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.Column('frequency', sa.Enum('ANNUAL', 'MONTHLY', name='frequency'), nullable=False),
                    sa.ForeignKeyConstraint(['income_type_id'], ['income_types.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('monthly_expenses',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('expense_type_id', sa.Integer(), nullable=True),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['expense_type_id'], ['expense_types.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('candidate_contact_numbers',
                    sa.Column('candidate_id', sa.Integer(), nullable=False),
                    sa.Column('contact_number_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['contact_number_id'], ['contact_numbers.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'contact_number_id')
                    )
    op.create_table('candidate_income_sources',
                    sa.Column('candidate_id', sa.Integer(), nullable=False),
                    sa.Column('income_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['income_id'], ['income_sources.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'income_id')
                    )
    op.create_table('candidate_monthly_expenses',
                    sa.Column('candidate_id', sa.Integer(), nullable=False),
                    sa.Column('expense_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['expense_id'], ['monthly_expenses.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'expense_id')
                    )
    op.create_table('client_income_sources',
                    sa.Column('client_id', sa.Integer(), nullable=False),
                    sa.Column('income_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
                    sa.ForeignKeyConstraint(['income_id'], ['income_sources.id'], ),
                    sa.PrimaryKeyConstraint('client_id', 'income_id')
                    )
    op.create_table('client_monthly_expenses',
                    sa.Column('candidate_id', sa.Integer(), nullable=False),
                    sa.Column('expense_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['clients.id'], ),
                    sa.ForeignKeyConstraint(['expense_id'], ['monthly_expenses.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'expense_id')
                    )
    op.drop_table('candidate_contact_number')
    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.add_column(sa.Column('client_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('county', sa.String(length=50), nullable=True))
        batch_op.add_column(
            sa.Column('employment_status', sa.Enum('EMPLOYED', 'RETIRED', 'STUDENT', 'UNEMPLOYED', name='employmentstatus'), nullable=True))
        batch_op.create_foreign_key('client_id', 'clients', ['client_id'], ['id'])

    with op.batch_alter_table('employments', schema=None) as batch_op:
        batch_op.alter_column('other_income',
                              existing_type=sa.FLOAT(),
                              nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('employments', schema=None) as batch_op:
        batch_op.alter_column('other_income',
                              existing_type=sa.FLOAT(),
                              nullable=False)

    with op.batch_alter_table('clients', schema=None) as batch_op:
        batch_op.drop_constraint('client_id', type_='foreignkey')
        batch_op.drop_column('employment_status')
        batch_op.drop_column('county')
        batch_op.drop_column('client_id')

    op.create_table('candidate_contact_number',
                    sa.Column('candidate_id', sa.INTEGER(), nullable=False),
                    sa.Column('contact_number_id', sa.INTEGER(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['contact_number_id'], ['contact_numbers.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'contact_number_id')
                    )
    op.drop_table('client_monthly_expenses')
    op.drop_table('client_income_sources')
    op.drop_table('candidate_monthly_expenses')
    op.drop_table('candidate_income_sources')
    op.drop_table('candidate_contact_numbers')
    op.drop_table('monthly_expenses')
    op.drop_table('income_sources')
    op.drop_table('income_types')
    op.drop_table('expense_types')
    # ### end Alembic commands ###
