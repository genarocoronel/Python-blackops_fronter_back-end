"""empty message

Revision ID: d0ef08231b2f
Revises: f046787c1b38
Create Date: 2020-05-04 20:53:51.291654

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd0ef08231b2f'
down_revision = 'f046787c1b38'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('appointment_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('appointment_id', sa.Integer(), nullable=True),
    sa.Column('content', sa.String(length=1000), nullable=False),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], name='appointment_notes_appointment_id_fkey'),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name='appointment_notes_author_id_fkey'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('appointments', sa.Column('agent_id', sa.Integer(), nullable=True))
    op.add_column('appointments', sa.Column('created_date', sa.DateTime(), nullable=True))
    op.add_column('appointments', sa.Column('location', sa.String(length=255), nullable=False))
    op.add_column('appointments', sa.Column('modified_date', sa.DateTime(), nullable=True))
    op.add_column('appointments', sa.Column('scheduled_at', sa.DateTime(), nullable=False))
    op.add_column('appointments', sa.Column('team_manager_id', sa.Integer(), nullable=True))
    op.alter_column('appointments', 'client_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_foreign_key('appointments_team_manager_id_fkey', 'appointments', 'users', ['team_manager_id'], ['id'])
    op.create_foreign_key('appointments_agent_id_fkey', 'appointments', 'users', ['agent_id'], ['id'])
    op.create_foreign_key('appointments_client_id_fkey', 'appointments', 'clients', ['client_id'], ['id'])
    op.drop_column('appointments', 'employee_id')
    op.drop_column('appointments', 'notes')
    op.drop_column('appointments', 'datetime')
    # ### end Alembic commands ###
    ## non Alembic 
    op.alter_column('users',
                    'department',
                    type_=sa.VARCHAR(length=20),
                    nullable=True)
    op.alter_column('user_tasks',
                    'status',
                    type_=sa.VARCHAR(length=40),
                    nullable=True)
    op.alter_column('user_tasks',
                    'priority',
                    type_=sa.VARCHAR(length=240),
                    nullable=True)



def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('appointments', sa.Column('datetime', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.add_column('appointments', sa.Column('notes', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('appointments', sa.Column('employee_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint('appointments_client_id_fkey', 'appointments', type_='foreignkey')
    op.drop_constraint('appointments_agent_id_fkey', 'appointments', type_='foreignkey')
    op.drop_constraint('appointments_team_manager_id_fkey', 'appointments', type_='foreignkey')
    op.alter_column('appointments', 'client_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('appointments', 'team_manager_id')
    op.drop_column('appointments', 'scheduled_at')
    op.drop_column('appointments', 'modified_date')
    op.drop_column('appointments', 'location')
    op.drop_column('appointments', 'created_date')
    op.drop_column('appointments', 'agent_id')
    op.drop_table('appointment_notes')
    # ### end Alembic commands ###