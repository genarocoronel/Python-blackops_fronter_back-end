"""empty message

Revision ID: 9457beb425de
Revises: 
Create Date: 2019-12-07 17:01:02.799510

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
from app.main.seed.candidate_dispositions import seed_candidate_disposition_values
from app.main.seed.contact_number_types import seed_contact_number_types

revision = '9457beb425de'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('appointments',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('client_id', sa.Integer(), nullable=False),
                    sa.Column('employee_id', sa.Integer(), nullable=False),
                    sa.Column('datetime', sa.DateTime(), nullable=False),
                    sa.Column('summary', sa.String(length=255), nullable=False),
                    sa.Column('notes', sa.TEXT(), nullable=True),
                    sa.Column('reminder_types', sa.String(length=64), nullable=True),
                    sa.Column('status', sa.String(length=64), nullable=False),
                    sa.Column('public_id', sa.String(length=100), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('public_id')
                    )
    op.create_table('blacklist_tokens',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('token', sa.String(length=500), nullable=False),
                    sa.Column('blacklisted_on', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('token')
                    )
    op.create_table('campaigns',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('public_id', sa.String(length=100), nullable=True),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('phone', sa.String(length=25), nullable=False),
                    sa.Column('job_number', sa.String(length=25), nullable=False),
                    sa.Column('mailing_date', sa.String(length=10), nullable=False),
                    sa.Column('offer_expire_date', sa.String(length=10), nullable=False),
                    sa.Column('mailer_file', sa.String(length=100), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('job_number'),
                    sa.UniqueConstraint('mailer_file'),
                    sa.UniqueConstraint('name'),
                    sa.UniqueConstraint('public_id')
                    )
    candidate_dispositions = op.create_table('candidate_dispositions',
                                             sa.Column('id', sa.Integer(), nullable=False),
                                             sa.Column('public_id', sa.String(length=100), nullable=False),
                                             sa.Column('inserted_on', sa.DateTime(), nullable=False),
                                             sa.Column('value', sa.String(length=100), nullable=False),
                                             sa.Column('description', sa.String(length=255), nullable=True),
                                             sa.PrimaryKeyConstraint('id'),
                                             sa.UniqueConstraint('public_id'),
                                             sa.UniqueConstraint('value')
                                             )

    op.bulk_insert(candidate_dispositions, seed_candidate_disposition_values())

    op.create_table('candidate_imports',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('public_id', sa.String(length=100), nullable=False),
                    sa.Column('file', sa.String(length=255), nullable=False),
                    sa.Column('status', sa.Enum('CREATED', 'RECEIVED', 'RUNNING', 'FINISHED', 'ERROR', name='candidateimportstatus'),
                              nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('updated_on', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('public_id')
                    )
    op.create_table('clients',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('public_id', sa.String(length=100), nullable=True),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('suffix', sa.String(length=25), nullable=True),
                    sa.Column('first_name', sa.String(length=25), nullable=False),
                    sa.Column('middle_initial', sa.CHAR(), nullable=True),
                    sa.Column('last_name', sa.String(length=25), nullable=False),
                    sa.Column('address', sa.String(length=100), nullable=False),
                    sa.Column('city', sa.String(length=50), nullable=False),
                    sa.Column('state', sa.String(length=2), nullable=False),
                    sa.Column('zip', sa.Integer(), nullable=False),
                    sa.Column('zip4', sa.Integer(), nullable=False),
                    sa.Column('estimated_debt', sa.Integer(), nullable=False),
                    sa.Column('email', sa.String(length=255), nullable=True),
                    sa.Column('language', sa.String(length=25), nullable=True),
                    sa.Column('phone', sa.String(length=25), nullable=True),
                    sa.Column('type', sa.Enum('candidate', 'lead', 'client', name='clienttype'), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email'),
                    sa.UniqueConstraint('public_id')
                    )
    contact_number_types = op.create_table('contact_number_types',
                                           sa.Column('id', sa.Integer(), nullable=False),
                                           sa.Column('inserted_on', sa.DateTime(), nullable=False),
                                           sa.Column('name', sa.String(length=50), nullable=False),
                                           sa.Column('description', sa.Text(), nullable=True),
                                           sa.PrimaryKeyConstraint('id'),
                                           sa.UniqueConstraint('name')
                                           )

    op.bulk_insert(contact_number_types, seed_contact_number_types())

    op.create_table('docusign_template',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=200), nullable=False),
                    sa.Column('ds_key', sa.String(length=200), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('ds_key')
                    )
    op.create_table('employments',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('employer_name', sa.String(length=50), nullable=False),
                    sa.Column('start_date', sa.DateTime(), nullable=False),
                    sa.Column('end_date', sa.DateTime(), nullable=True),
                    sa.Column('gross_salary', sa.Float(), nullable=False),
                    sa.Column('gross_salary_frequency', sa.Enum('ANNUAL', 'MONTHLY', name='frequencystatus'), nullable=True),
                    sa.Column('other_income', sa.Float(), nullable=False),
                    sa.Column('other_income_frequency', sa.Enum('ANNUAL', 'MONTHLY', name='frequencystatus'), nullable=True),
                    sa.Column('current', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('sms_messages',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('message_provider_id', sa.String(length=50), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('text', sa.TEXT(), nullable=False),
                    sa.Column('phone_target', sa.String(length=25), nullable=False),
                    sa.Column('status', sa.String(length=25), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('first_name', sa.String(length=25), nullable=False),
                    sa.Column('last_name', sa.String(length=25), nullable=False),
                    sa.Column('email', sa.String(length=255), nullable=False),
                    sa.Column('registered_on', sa.DateTime(), nullable=False),
                    sa.Column('admin', sa.Boolean(), nullable=False),
                    sa.Column('require_2fa', sa.Boolean(), nullable=True),
                    sa.Column('title', sa.String(length=100), nullable=True),
                    sa.Column('language', sa.String(length=25), nullable=False),
                    sa.Column('personal_phone', sa.String(length=25), nullable=False),
                    sa.Column('voip_route_number', sa.String(length=50), nullable=True),
                    sa.Column('public_id', sa.String(length=100), nullable=True),
                    sa.Column('username', sa.String(length=50), nullable=False),
                    sa.Column('password_hash', sa.String(length=100), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email'),
                    sa.UniqueConstraint('public_id'),
                    sa.UniqueConstraint('username')
                    )
    op.create_table('bank_accounts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('client_id', sa.Integer(), nullable=True),
                    sa.Column('name', sa.String(length=125), nullable=False),
                    sa.Column('account_number', sa.String(length=100), nullable=False),
                    sa.Column('routing_number', sa.String(length=100), nullable=False),
                    sa.Column('valid', sa.Boolean(), nullable=False),
                    sa.Column('type', sa.Enum('checking', 'savings', name='bankaccounttype'), nullable=True),
                    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('candidates',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('public_id', sa.String(length=100), nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('disposition_id', sa.Integer(), nullable=True),
                    sa.Column('import_id', sa.Integer(), nullable=True),
                    sa.Column('campaign_id', sa.Integer(), nullable=True),
                    sa.Column('first_name', sa.String(length=25), nullable=False),
                    sa.Column('middle_initial', sa.CHAR(), nullable=True),
                    sa.Column('last_name', sa.String(length=25), nullable=False),
                    sa.Column('suffix', sa.String(length=25), nullable=True),
                    sa.Column('address', sa.String(length=100), nullable=False),
                    sa.Column('city', sa.String(length=50), nullable=False),
                    sa.Column('state', sa.String(length=2), nullable=False),
                    sa.Column('zip', sa.String(length=5), nullable=False),
                    sa.Column('zip4', sa.String(length=4), nullable=False),
                    sa.Column('status', sa.Enum('IMPORTED', 'CAMPAIGNED', 'WORKING', 'SUBMITTED', name='candidatestatus'), nullable=True),
                    sa.Column('estimated_debt', sa.Integer(), nullable=False),
                    sa.Column('prequal_number', sa.String(length=12), nullable=True),
                    sa.Column('debt3', sa.Integer(), nullable=False),
                    sa.Column('debt15', sa.Integer(), nullable=False),
                    sa.Column('debt2', sa.Integer(), nullable=False),
                    sa.Column('debt215', sa.Integer(), nullable=False),
                    sa.Column('debt3_2', sa.Integer(), nullable=False),
                    sa.Column('checkamt', sa.Integer(), nullable=False),
                    sa.Column('spellamt', sa.String(length=100), nullable=False),
                    sa.Column('debt315', sa.Integer(), nullable=False),
                    sa.Column('year_interest', sa.Integer(), nullable=False),
                    sa.Column('total_interest', sa.Integer(), nullable=False),
                    sa.Column('sav215', sa.Integer(), nullable=False),
                    sa.Column('sav15', sa.Integer(), nullable=False),
                    sa.Column('sav315', sa.Integer(), nullable=False),
                    sa.Column('county', sa.String(length=50), nullable=True),
                    sa.Column('email', sa.String(length=255), nullable=True),
                    sa.Column('language', sa.String(length=25), nullable=True),
                    sa.Column('phone', sa.String(length=25), nullable=True),
                    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
                    sa.ForeignKeyConstraint(['disposition_id'], ['candidate_dispositions.id'], ),
                    sa.ForeignKeyConstraint(['import_id'], ['candidate_imports.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email'),
                    sa.UniqueConstraint('prequal_number'),
                    sa.UniqueConstraint('public_id')
                    )
    op.create_table('client_employments',
                    sa.Column('client_id', sa.Integer(), nullable=False),
                    sa.Column('employment_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
                    sa.ForeignKeyConstraint(['employment_id'], ['employments.id'], ),
                    sa.PrimaryKeyConstraint('client_id', 'employment_id')
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
    op.create_table('docusign_signature',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('envelope_id', sa.String(length=200), nullable=False),
                    sa.Column('status',
                              sa.Enum('SENT', 'CREATED', 'DELIVERED', 'COMPLETED', 'DECLINED', 'SIGNED', 'VOIDED', name='signaturestatus'),
                              nullable=False),
                    sa.Column('created_date', sa.DateTime(), nullable=True),
                    sa.Column('client_id', sa.Integer(), nullable=False),
                    sa.Column('template_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
                    sa.ForeignKeyConstraint(['template_id'], ['docusign_template.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('envelope_id')
                    )
    op.create_table('import_tasks',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('name', sa.String(length=128), nullable=True),
                    sa.Column('description', sa.String(length=128), nullable=True),
                    sa.Column('message', sa.String(length=255), nullable=True),
                    sa.Column('import_id', sa.Integer(), nullable=True),
                    sa.Column('complete', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['import_id'], ['candidate_imports.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    with op.batch_alter_table('import_tasks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_import_tasks_name'), ['name'], unique=False)

    op.create_table('password_resets',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('reset_key', sa.String(length=128), nullable=True),
                    sa.Column('code_hash', sa.String(length=100), nullable=True),
                    sa.Column('validated', sa.Boolean(), nullable=True),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('datetime', sa.DateTime(timezone=True), nullable=True),
                    sa.Column('has_activated', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('reset_key')
                    )
    op.create_table('candidate_contact_number',
                    sa.Column('candidate_id', sa.Integer(), nullable=False),
                    sa.Column('contact_number_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['contact_number_id'], ['contact_numbers.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'contact_number_id')
                    )
    op.create_table('candidate_employments',
                    sa.Column('candidate_id', sa.Integer(), nullable=False),
                    sa.Column('employment_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['employment_id'], ['employments.id'], ),
                    sa.PrimaryKeyConstraint('candidate_id', 'employment_id')
                    )
    op.create_table('credit_report_accounts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('public_id', sa.String(length=100), nullable=True),
                    sa.Column('candidate_id', sa.Integer(), nullable=True),
                    sa.Column('client_id', sa.Integer(), nullable=True),
                    sa.Column('provider', sa.String(length=50), nullable=False),
                    sa.Column('customer_token', sa.String(), nullable=True),
                    sa.Column('tracking_token', sa.String(length=100), nullable=False),
                    sa.Column('plan_type', sa.String(length=50), nullable=True),
                    sa.Column('financial_obligation_met', sa.Boolean(), nullable=True),
                    sa.Column('password_enc', sa.String(length=128), nullable=True),
                    sa.Column('status',
                              sa.Enum('INITIATING_SIGNUP', 'ACCOUNT_CREATED', 'ACCOUNT_VALIDATING', 'ACCOUNT_VALIDATED', 'FULL_MEMBER',
                                      name='creditreportsignupstatus'), nullable=False),
                    sa.Column('email', sa.String(length=30), nullable=True),
                    sa.Column('registered_fraud_insurance', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
                    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], name='fk_client'),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('customer_token'),
                    sa.UniqueConstraint('email'),
                    sa.UniqueConstraint('public_id')
                    )
    op.create_table('credit_report_data',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('last_update', sa.DateTime(), nullable=True),
                    sa.Column('account_id', sa.Integer(), nullable=True),
                    sa.Column('debt_name', sa.String(length=100), nullable=True),
                    sa.Column('creditor', sa.String(length=100), nullable=True),
                    sa.Column('ecoa', sa.String(length=50), nullable=True),
                    sa.Column('account_number', sa.String(length=25), nullable=True),
                    sa.Column('account_type', sa.String(length=100), nullable=True),
                    sa.Column('push', sa.Boolean(), nullable=True),
                    sa.Column('last_collector', sa.String(length=100), nullable=True),
                    sa.Column('collector_account', sa.String(length=100), nullable=True),
                    sa.Column('last_debt_status', sa.String(length=100), nullable=True),
                    sa.Column('bureaus', sa.String(length=100), nullable=True),
                    sa.Column('days_delinquent', sa.String(length=20), nullable=True),
                    sa.Column('balance_original', sa.String(length=20), nullable=True),
                    sa.Column('payment_amount', sa.String(length=20), nullable=True),
                    sa.Column('credit_limit', sa.String(length=20), nullable=True),
                    sa.Column('graduation', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['account_id'], ['credit_report_accounts.id'], name='fk_credit_report_data'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('scrape_tasks',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('inserted_on', sa.DateTime(), nullable=False),
                    sa.Column('updated_on', sa.DateTime(), nullable=True),
                    sa.Column('account_id', sa.Integer(), nullable=True),
                    sa.Column('name', sa.String(length=128), nullable=True),
                    sa.Column('complete', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['account_id'], ['credit_report_accounts.id'], name='fk_scrape_tasks'),
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
    op.drop_table('credit_report_accounts')
    op.drop_table('candidate_employments')
    op.drop_table('candidate_contact_number')
    op.drop_table('password_resets')
    with op.batch_alter_table('import_tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_import_tasks_name'))

    op.drop_table('import_tasks')
    op.drop_table('docusign_signature')
    op.drop_table('contact_numbers')
    op.drop_table('client_employments')
    op.drop_table('candidates')
    op.drop_table('bank_accounts')
    op.drop_table('users')
    op.drop_table('sms_messages')
    op.drop_table('employments')
    op.drop_table('docusign_template')
    op.drop_table('contact_number_types')
    op.drop_table('clients')
    op.drop_table('candidate_imports')
    op.drop_table('candidate_dispositions')
    op.drop_table('campaigns')
    op.drop_table('blacklist_tokens')
    op.drop_table('appointments')
    # ### end Alembic commands ###