"""empty message

Revision ID: a05ed97bab59
Revises: b2351f5cb21d
Create Date: 2019-11-24 20:53:13.921059

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a05ed97bab59'
down_revision = 'b2351f5cb21d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('credit_report_data',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('candidate_id', sa.Integer(), nullable=True),
    sa.Column('public_id', sa.String(length=100), nullable=True),
    sa.Column('debt_name', sa.String(length=100), nullable=True),
    sa.Column('creditor', sa.String(length=100), nullable=True),
    sa.Column('ecoa', sa.String(length=50), nullable=True),
    sa.Column('account_number', sa.String(length=25), nullable=True),
    sa.Column('account_type', sa.String(length=25), nullable=True),
    sa.Column('push', sa.Boolean(), nullable=True),
    sa.Column('last_collector', sa.String(length=100), nullable=True),
    sa.Column('collector_account', sa.String(length=100), nullable=True),
    sa.Column('last_debt_status', sa.String(length=100), nullable=True),
    sa.Column('bureaus', sa.String(length=100), nullable=True),
    sa.Column('days_delinquent', sa.String(length=20), nullable=True),
    sa.Column('balance_original', sa.String(length=20), nullable=True),
    sa.Column('payment_amount', sa.String(length=20), nullable=True),
    sa.Column('credit_limit', sa.String(length=20), nullable=True),
    sa.Column('graduation', sa.String(length=30), nullable=True),
    sa.Column('last_update', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id')
    )
    op.create_table('scrape_tasks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=128), nullable=True),
    sa.Column('candidate_id', sa.Integer(), nullable=True),
    sa.Column('inserted_on', sa.DateTime(), nullable=False),
    sa.Column('updated_on', sa.DateTime(), nullable=True),
    sa.Column('complete', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('scrape_tasks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_scrape_tasks_name'), ['name'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('scrape_tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_scrape_tasks_name'))

    op.drop_table('scrape_tasks')
    op.drop_table('credit_report_data')
    # ### end Alembic commands ###
