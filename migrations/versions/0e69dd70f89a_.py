"""empty message

Revision ID: 0e69dd70f89a
Revises: bc35d8dcc5e1
Create Date: 2020-02-25 02:17:23.707118

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0e69dd70f89a'
down_revision = 'bc35d8dcc5e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sms_bandwidth',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('inserted_on', sa.DateTime(), nullable=True),
    sa.Column('is_imported', sa.Boolean(), nullable=True),
    sa.Column('time', sa.String(length=25), nullable=True),
    sa.Column('type', sa.String(length=50), nullable=True),
    sa.Column('to', sa.String(length=20), nullable=True),
    sa.Column('description', sa.String(length=25), nullable=True),
    sa.Column('message_id', sa.String(length=100), nullable=True),
    sa.Column('message_owner', sa.String(length=20), nullable=True),
    sa.Column('message_application_id', sa.String(length=100), nullable=True),
    sa.Column('message_time', sa.String(length=25), nullable=True),
    sa.Column('message_segment_count', sa.Integer(), nullable=True),
    sa.Column('message_direction', sa.String(length=20), nullable=True),
    sa.Column('message_to', sa.String(length=100), nullable=True),
    sa.Column('message_from', sa.String(length=20), nullable=True),
    sa.Column('message_text', sa.String(length=918), nullable=True),
    sa.Column('message_media', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sms_media_files',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('public_id', sa.String(length=100), nullable=True),
    sa.Column('inserted_on', sa.DateTime(), nullable=True),
    sa.Column('file_uri', sa.String(length=500), nullable=True),
    sa.Column('fk_sms_message', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['fk_sms_message'], ['sms_messages.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id'),
    )
    op.create_table('sms_convos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('public_id', sa.String(length=100), nullable=True),
    sa.Column('inserted_on', sa.DateTime(), nullable=True),
    sa.Column('updated_on', sa.DateTime(), nullable=True),
    sa.Column('client_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='fk_client'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('public_id'),
    )
    with op.batch_alter_table('sms_messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('body_text', sa.String(length=918), nullable=True))
        batch_op.add_column(sa.Column('direction', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('from_phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('inserted_on', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('is_viewed', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('network_time', sa.String(length=25), nullable=True))
        batch_op.add_column(sa.Column('provider_message_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('provider_name', sa.String(length=25), nullable=True))
        batch_op.add_column(sa.Column('public_id', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('segment_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('sms_convo_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('to_phone', sa.String(length=20), nullable=True))
        batch_op.create_foreign_key('fk_sms_convos_id', 'sms_convos', ['sms_convo_id'], ['id'])
        batch_op.create_unique_constraint('sms_uq_convos_public_id', ['public_id']),
        batch_op.drop_column('phone_target')
        batch_op.drop_column('status')
        batch_op.drop_column('user_id')
        batch_op.drop_column('text')
        batch_op.drop_column('message_provider_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sms_messages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('message_provider_id', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('text', sa.TEXT(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('status', sa.VARCHAR(length=25), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('phone_target', sa.VARCHAR(length=25), autoincrement=False, nullable=False))
        batch_op.drop_constraint('fk_sms_convos_id', type_='foreignkey')
        batch_op.drop_constraint('sms_uq_convos_public_id', type_='unique')
        batch_op.drop_column('to_phone')
        batch_op.drop_column('sms_convo_id')
        batch_op.drop_column('segment_count')
        batch_op.drop_column('public_id')
        batch_op.drop_column('provider_name')
        batch_op.drop_column('provider_message_id')
        batch_op.drop_column('network_time')
        batch_op.drop_column('is_viewed')
        batch_op.drop_column('inserted_on')
        batch_op.drop_column('from_phone')
        batch_op.drop_column('direction')
        batch_op.drop_column('body_text')

    op.drop_table('sms_convos')
    op.drop_table('sms_media_files')
    op.drop_table('sms_bandwidth')
    # ### end Alembic commands ###
