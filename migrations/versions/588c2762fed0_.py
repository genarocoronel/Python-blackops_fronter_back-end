"""empty message

Revision ID: 588c2762fed0
Revises: bc35d8dcc5e1
Create Date: 2020-02-27 14:36:48.122815

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session


# revision identifiers, used by Alembic.
revision = '588c2762fed0'
down_revision = '0e69dd70f89a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('checklist',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('client_checklist',
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('checklist_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['checklist_id'], ['checklist.id'], ),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('client_id', 'checklist_id')
    )
    op.create_table('notification_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=True),
    sa.Column('service_call', sa.Enum('HOME', 'WORK', 'MOBILE', name='calloptions'), nullable=False),
    sa.Column('appt_reminder', sa.Enum('TEXT', 'EMAIL', 'CALL', 'NONE', name='apptreminderoptions'), nullable=False),
    sa.Column('doc_notification', sa.Enum('TEXT', 'EMAIL', 'POST', 'FAX', name='docnotificationoptions'), nullable=False),
    sa.Column('payment_reminder', sa.Enum('EMAIL', 'CALL', 'NONE', name='pymtreminderoptions'), nullable=False),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    session = Session(bind=op.get_bind())
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('notification_preferences')
    op.drop_table('client_checklist')
    op.drop_table('checklist')
    if 'postgresql' in session.bind.dialect.name:
        # drop enums
        op.execute('DROP TYPE calloptions')
        op.execute('DROP TYPE apptreminderoptions')
        op.execute('DROP TYPE docnotificationoptions')
        op.execute('DROP TYPE pymtreminderoptions')
    # ### end Alembic commands ###
