"""Added new enum val in revisionmethod

Revision ID: 5e6b1d89b5d7
Revises: 9a39c01a9f0e
Create Date: 2020-10-08 17:18:00.891355

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e6b1d89b5d7'
down_revision = '9a39c01a9f0e'
branch_labels = None
depends_on = None

old_options = ('SKIP_PAYMENT', 'CHANGE_DRAFT_DATE', 'CHANGE_RECUR_DAY', 'MANUAL_ADJUSTMENT', 'REFUND', 'RE_INSTATE', 'ADD_TO_EFT')
new_options = sorted(old_options + ('NSF_REDRAFT',))

old_type = sa.Enum(*old_options, name='revisionmethod')
new_type = sa.Enum(*new_options, name='revisionmethod')
tmp_type = sa.Enum(*new_options, name='_revisionmethod')

def upgrade():
    # manual edited
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE debt_payment_contract_revision ALTER COLUMN method TYPE _revisionmethod'
               ' USING method::text::_revisionmethod')
    old_type.drop(op.get_bind(), checkfirst=False)
    new_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE debt_payment_contract_revision ALTER COLUMN method TYPE revisionmethod'
               ' USING method::text::revisionmethod')
    tmp_type.drop(op.get_bind(), checkfirst=False) 
  

def downgrade():
    # manual edited
    tmp_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE debt_payment_contract_revision ALTER COLUMN method TYPE _revisionmethod'
               ' USING method::text::_revisionmethod')
    new_type.drop(op.get_bind(), checkfirst=False)
    old_type.create(op.get_bind(), checkfirst=False)
    op.execute('ALTER TABLE debt_payment_contract_revision ALTER COLUMN method TYPE revisionmethod'
               ' USING method::text::revisionmethod')
    tmp_type.drop(op.get_bind(), checkfirst=False)
    
