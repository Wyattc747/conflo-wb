"""initial_schema

Revision ID: 5502d0130dfa
Revises: 
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '5502d0130dfa'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('''\nCREATE TABLE notifications (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	user_type VARCHAR(20) NOT NULL, 
	user_id UUID NOT NULL, 
	type VARCHAR(50) NOT NULL, 
	title VARCHAR NOT NULL, 
	body TEXT, 
	source_type VARCHAR(50), 
	source_id UUID, 
	read_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)\n''')

    op.execute('''\nCREATE TABLE organizations (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	name VARCHAR NOT NULL, 
	logo_url VARCHAR, 
	address_line1 VARCHAR, 
	address_line2 VARCHAR, 
	city VARCHAR, 
	state VARCHAR, 
	zip_code VARCHAR, 
	phone VARCHAR, 
	license_numbers JSONB DEFAULT '{}'::jsonb NOT NULL, 
	timezone VARCHAR(50) DEFAULT 'America/Denver' NOT NULL, 
	stripe_customer_id VARCHAR, 
	subscription_tier VARCHAR(20) DEFAULT 'STARTER' NOT NULL, 
	subscription_status VARCHAR(20) DEFAULT 'TRIALING' NOT NULL, 
	stripe_subscription_id VARCHAR, 
	contract_start_date TIMESTAMP WITH TIME ZONE, 
	contract_end_date TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (stripe_customer_id)
)\n''')

    op.execute('''\nCREATE TABLE owner_accounts (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	name VARCHAR NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)\n''')

    op.execute('''\nCREATE TABLE sub_companies (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	name VARCHAR NOT NULL, 
	address VARCHAR, 
	phone VARCHAR, 
	website VARCHAR, 
	primary_contact_user_id UUID, 
	trades JSONB DEFAULT '[]'::jsonb NOT NULL, 
	certifications JSONB DEFAULT '[]'::jsonb NOT NULL, 
	insurance_coi_url VARCHAR, 
	insurance_expiry_date TIMESTAMP WITH TIME ZONE, 
	bonding_single_limit NUMERIC(15, 2), 
	bonding_aggregate_limit NUMERIC(15, 2), 
	license_numbers JSONB DEFAULT '{}'::jsonb NOT NULL, 
	service_area VARCHAR, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
)\n''')

    op.execute('''\nCREATE TABLE audit_logs (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID, 
	actor_id UUID, 
	action VARCHAR(50) NOT NULL, 
	resource_type VARCHAR(50) NOT NULL, 
	resource_id UUID, 
	before_data JSONB DEFAULT '{}'::jsonb NOT NULL, 
	after_data JSONB DEFAULT '{}'::jsonb NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)\n''')

    op.execute('''\nCREATE TABLE comments (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	commentable_type VARCHAR(50) NOT NULL, 
	commentable_id UUID NOT NULL, 
	author_type VARCHAR(20) NOT NULL, 
	author_id UUID NOT NULL, 
	body TEXT NOT NULL, 
	is_official_response BOOLEAN DEFAULT false NOT NULL, 
	attachment_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	mentioned_user_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)\n''')

    op.execute('''\nCREATE TABLE contacts (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	company_name VARCHAR, 
	contact_name VARCHAR, 
	email VARCHAR, 
	phone VARCHAR, 
	category VARCHAR(30) DEFAULT 'OTHER' NOT NULL, 
	trade VARCHAR, 
	address VARCHAR, 
	notes TEXT, 
	linked_sub_company_id UUID, 
	linked_owner_account_id UUID, 
	status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(linked_sub_company_id) REFERENCES sub_companies (id), 
	FOREIGN KEY(linked_owner_account_id) REFERENCES owner_accounts (id)
)\n''')

    op.execute('''\nCREATE TABLE cost_code_templates (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	codes JSONB DEFAULT '[]'::jsonb NOT NULL, 
	is_default BOOLEAN DEFAULT false NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)\n''')

    op.execute('''\nCREATE TABLE inspection_templates (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	fields JSONB DEFAULT '[]'::jsonb NOT NULL, 
	is_default BOOLEAN DEFAULT false NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)\n''')

    op.execute('''\nCREATE TABLE integration_connections (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	provider VARCHAR(50) NOT NULL, 
	access_token_enc VARCHAR, 
	refresh_token_enc VARCHAR, 
	config JSONB DEFAULT '{}'::jsonb NOT NULL, 
	status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id)
)\n''')

    op.execute('''\nCREATE TABLE invitations (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	email VARCHAR NOT NULL, 
	user_type VARCHAR(20) NOT NULL, 
	permission_level VARCHAR(20), 
	token VARCHAR NOT NULL, 
	status VARCHAR(20) DEFAULT 'PENDING' NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	UNIQUE (token)
)\n''')

    op.execute('''\nCREATE TABLE owner_users (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	owner_account_id UUID NOT NULL, 
	clerk_user_id VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	phone VARCHAR, 
	title VARCHAR, 
	status VARCHAR(20) DEFAULT 'INVITED' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_account_id) REFERENCES owner_accounts (id), 
	UNIQUE (clerk_user_id)
)\n''')

    op.execute('''\nCREATE TABLE sub_users (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	sub_company_id UUID NOT NULL, 
	clerk_user_id VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	phone VARCHAR, 
	title VARCHAR, 
	is_primary BOOLEAN DEFAULT false NOT NULL, 
	status VARCHAR(20) DEFAULT 'INVITED' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sub_company_id) REFERENCES sub_companies (id), 
	UNIQUE (clerk_user_id)
)\n''')

    op.execute('''\nCREATE TABLE users (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	clerk_user_id VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	phone VARCHAR, 
	title VARCHAR, 
	avatar_url VARCHAR, 
	permission_level VARCHAR(20) NOT NULL, 
	status VARCHAR(20) DEFAULT 'INVITED' NOT NULL, 
	notification_preferences JSONB DEFAULT '{}'::jsonb NOT NULL, 
	timezone VARCHAR(50), 
	last_active_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	UNIQUE (clerk_user_id)
)\n''')

    op.execute('''\nCREATE TABLE projects (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	name VARCHAR NOT NULL, 
	project_number VARCHAR, 
	address VARCHAR, 
	city VARCHAR, 
	state VARCHAR, 
	zip_code VARCHAR, 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	timezone VARCHAR(50), 
	project_type VARCHAR(30) DEFAULT 'COMMERCIAL' NOT NULL, 
	contract_value NUMERIC(15, 2), 
	is_major BOOLEAN GENERATED ALWAYS AS (contract_value >= 250000) STORED, 
	phase VARCHAR(20) DEFAULT 'BIDDING' NOT NULL, 
	estimated_start_date TIMESTAMP WITH TIME ZONE, 
	estimated_end_date TIMESTAMP WITH TIME ZONE, 
	actual_start_date TIMESTAMP WITH TIME ZONE, 
	actual_end_date TIMESTAMP WITH TIME ZONE, 
	owner_client_name VARCHAR, 
	owner_client_company VARCHAR, 
	ae_name VARCHAR, 
	ae_company VARCHAR, 
	cost_code_template_id UUID, 
	bid_due_date TIMESTAMP WITH TIME ZONE, 
	created_by_user_id UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	deleted_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(cost_code_template_id) REFERENCES cost_code_templates (id), 
	FOREIGN KEY(created_by_user_id) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE bid_packages (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	title VARCHAR NOT NULL, 
	description TEXT, 
	trades JSONB DEFAULT '[]'::jsonb NOT NULL, 
	bid_due_date TIMESTAMP WITH TIME ZONE, 
	invited_sub_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL, 
	awarded_sub_id UUID, 
	awarded_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(awarded_sub_id) REFERENCES sub_companies (id)
)\n''')

    op.execute('''\nCREATE TABLE budget_line_items (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	project_id UUID NOT NULL, 
	cost_code VARCHAR NOT NULL, 
	description VARCHAR, 
	original_amount NUMERIC(15, 2) DEFAULT 0 NOT NULL, 
	approved_changes NUMERIC(15, 2) DEFAULT 0 NOT NULL, 
	committed NUMERIC(15, 2) DEFAULT 0 NOT NULL, 
	actuals NUMERIC(15, 2) DEFAULT 0 NOT NULL, 
	projected NUMERIC(15, 2) DEFAULT 0 NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)\n''')

    op.execute('''\nCREATE TABLE change_orders (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	title VARCHAR NOT NULL, 
	order_type VARCHAR(10) DEFAULT 'PCO' NOT NULL, 
	reason TEXT, 
	description TEXT, 
	cost_breakdown JSONB DEFAULT '[]'::jsonb NOT NULL, 
	total_amount NUMERIC(15, 2), 
	schedule_impact_days INTEGER, 
	related_rfi_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	status VARCHAR(30) DEFAULT 'DRAFT' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE daily_logs (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	log_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	weather_data JSONB DEFAULT '{}'::jsonb NOT NULL, 
	manpower JSONB DEFAULT '[]'::jsonb NOT NULL, 
	work_performed TEXT, 
	delays JSONB DEFAULT '[]'::jsonb NOT NULL, 
	status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_daily_logs_project_date UNIQUE (project_id, log_date), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE drawings (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	title VARCHAR NOT NULL, 
	set_number VARCHAR, 
	discipline VARCHAR, 
	revision VARCHAR, 
	is_current_set BOOLEAN DEFAULT true NOT NULL, 
	received_date TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE event_logs (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID, 
	project_id UUID, 
	user_type VARCHAR(20), 
	user_id UUID, 
	event_type VARCHAR(100) NOT NULL, 
	event_data JSONB DEFAULT '{}'::jsonb NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)\n''')

    op.execute('''\nCREATE TABLE files (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID, 
	s3_key VARCHAR NOT NULL, 
	filename VARCHAR NOT NULL, 
	mime_type VARCHAR, 
	size_bytes INTEGER, 
	uploaded_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)\n''')

    op.execute('''\nCREATE TABLE inspections (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	title VARCHAR NOT NULL, 
	template_id UUID, 
	form_data JSONB DEFAULT '{}'::jsonb NOT NULL, 
	inspector_user_id UUID, 
	scheduled_date TIMESTAMP WITH TIME ZONE, 
	completed_date TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(20) DEFAULT 'SCHEDULED' NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(template_id) REFERENCES inspection_templates (id), 
	FOREIGN KEY(inspector_user_id) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE meetings (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	title VARCHAR NOT NULL, 
	scheduled_date TIMESTAMP WITH TIME ZONE, 
	location VARCHAR, 
	attendees JSONB DEFAULT '[]'::jsonb NOT NULL, 
	agenda TEXT, 
	minutes TEXT, 
	action_items JSONB DEFAULT '[]'::jsonb NOT NULL, 
	status VARCHAR(20) DEFAULT 'SCHEDULED' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)\n''')

    op.execute('''\nCREATE TABLE owner_portal_configs (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	project_id UUID NOT NULL, 
	show_schedule BOOLEAN DEFAULT true NOT NULL, 
	show_submittals BOOLEAN DEFAULT true NOT NULL, 
	show_rfis BOOLEAN DEFAULT true NOT NULL, 
	show_transmittals BOOLEAN DEFAULT true NOT NULL, 
	show_drawings BOOLEAN DEFAULT true NOT NULL, 
	show_punch_list BOOLEAN DEFAULT true NOT NULL, 
	show_budget_summary BOOLEAN DEFAULT false NOT NULL, 
	show_daily_logs BOOLEAN DEFAULT false NOT NULL, 
	allow_punch_creation BOOLEAN DEFAULT false NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (project_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)\n''')

    op.execute('''\nCREATE TABLE pay_apps (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	period_start TIMESTAMP WITH TIME ZONE NOT NULL, 
	period_end TIMESTAMP WITH TIME ZONE NOT NULL, 
	sov_data JSONB DEFAULT '[]'::jsonb NOT NULL, 
	retention_rate NUMERIC(5, 2) DEFAULT 10.00 NOT NULL, 
	submitted_by_type VARCHAR(20), 
	submitted_by_id UUID, 
	total_completed NUMERIC(15, 2), 
	total_retainage NUMERIC(15, 2), 
	net_payment_due NUMERIC(15, 2), 
	status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL, 
	submitted_at TIMESTAMP WITH TIME ZONE, 
	reviewed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE procurement_items (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	name VARCHAR NOT NULL, 
	description TEXT, 
	vendor VARCHAR, 
	po_number VARCHAR, 
	cost_code VARCHAR, 
	estimated_cost NUMERIC(15, 2), 
	actual_cost NUMERIC(15, 2), 
	dates JSONB DEFAULT '{}'::jsonb NOT NULL, 
	status VARCHAR(20) DEFAULT 'IDENTIFIED' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)\n''')

    op.execute('''\nCREATE TABLE project_assignments (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	project_id UUID NOT NULL, 
	assignee_type VARCHAR(20) NOT NULL, 
	assignee_id UUID NOT NULL, 
	financial_access BOOLEAN DEFAULT false NOT NULL, 
	bidding_access BOOLEAN DEFAULT false NOT NULL, 
	trade VARCHAR, 
	contract_value NUMERIC(15, 2), 
	assigned_by_user_id UUID, 
	assigned_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_project_assignment UNIQUE (project_id, assignee_type, assignee_id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(assigned_by_user_id) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE punch_list_items (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	title VARCHAR NOT NULL, 
	description TEXT, 
	location VARCHAR, 
	trade VARCHAR, 
	assigned_sub_company_id UUID, 
	priority VARCHAR(20) DEFAULT 'NORMAL' NOT NULL, 
	before_photo_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	after_photo_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	status VARCHAR(30) DEFAULT 'OPEN' NOT NULL, 
	due_date TIMESTAMP WITH TIME ZONE, 
	completed_at TIMESTAMP WITH TIME ZONE, 
	verified_at TIMESTAMP WITH TIME ZONE, 
	verified_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(assigned_sub_company_id) REFERENCES sub_companies (id)
)\n''')

    op.execute('''\nCREATE TABLE rfis (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	subject VARCHAR NOT NULL, 
	question TEXT NOT NULL, 
	assigned_to UUID, 
	priority VARCHAR(20) DEFAULT 'NORMAL' NOT NULL, 
	cost_impact BOOLEAN DEFAULT false NOT NULL, 
	schedule_impact BOOLEAN DEFAULT false NOT NULL, 
	due_date TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(20) DEFAULT 'DRAFT' NOT NULL, 
	official_response TEXT, 
	responded_by UUID, 
	responded_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(assigned_to) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE schedule_tasks (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	name VARCHAR NOT NULL, 
	start_date TIMESTAMP WITH TIME ZONE, 
	end_date TIMESTAMP WITH TIME ZONE, 
	duration INTEGER, 
	predecessors JSONB DEFAULT '[]'::jsonb NOT NULL, 
	assigned_to UUID, 
	percent_complete INTEGER DEFAULT 0 NOT NULL, 
	sort_order INTEGER DEFAULT 0 NOT NULL, 
	parent_task_id UUID, 
	milestone BOOLEAN DEFAULT false NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(parent_task_id) REFERENCES schedule_tasks (id)
)\n''')

    op.execute('''\nCREATE TABLE submittals (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	revision INTEGER DEFAULT 0 NOT NULL, 
	spec_section VARCHAR, 
	submittal_type VARCHAR(30), 
	title VARCHAR NOT NULL, 
	description TEXT, 
	reviewer_id UUID, 
	submitted_by_sub_id UUID, 
	status VARCHAR(30) DEFAULT 'DRAFT' NOT NULL, 
	due_date TIMESTAMP WITH TIME ZONE, 
	reviewed_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(reviewer_id) REFERENCES users (id), 
	FOREIGN KEY(submitted_by_sub_id) REFERENCES sub_companies (id)
)\n''')

    op.execute('''\nCREATE TABLE todos (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	title VARCHAR NOT NULL, 
	description TEXT, 
	assigned_to UUID, 
	due_date TIMESTAMP WITH TIME ZONE, 
	priority VARCHAR(20) DEFAULT 'NORMAL' NOT NULL, 
	status VARCHAR(20) DEFAULT 'TODO' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
)\n''')

    op.execute('''\nCREATE TABLE transmittals (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	number INTEGER NOT NULL, 
	subject VARCHAR NOT NULL, 
	to_contact_ids JSONB DEFAULT '[]'::jsonb NOT NULL, 
	action_required VARCHAR, 
	notes TEXT, 
	status VARCHAR(20) DEFAULT 'SENT' NOT NULL, 
	sent_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
)\n''')

    op.execute('''\nCREATE TABLE bid_submissions (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	bid_package_id UUID NOT NULL, 
	sub_company_id UUID NOT NULL, 
	total_amount NUMERIC(15, 2), 
	line_items JSONB DEFAULT '[]'::jsonb NOT NULL, 
	qualifications TEXT, 
	submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(bid_package_id) REFERENCES bid_packages (id), 
	FOREIGN KEY(sub_company_id) REFERENCES sub_companies (id)
)\n''')

    op.execute('''\nCREATE TABLE documents (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	organization_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	created_by UUID, 
	title VARCHAR NOT NULL, 
	category VARCHAR, 
	file_url VARCHAR, 
	file_id UUID, 
	version INTEGER DEFAULT 1 NOT NULL, 
	uploaded_by UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(organization_id) REFERENCES organizations (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(file_id) REFERENCES files (id)
)\n''')

    op.execute('''\nCREATE TABLE drawing_sheets (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	drawing_id UUID NOT NULL, 
	sheet_number VARCHAR NOT NULL, 
	title VARCHAR, 
	discipline VARCHAR, 
	file_id UUID, 
	revision VARCHAR, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(drawing_id) REFERENCES drawings (id), 
	FOREIGN KEY(file_id) REFERENCES files (id)
)\n''')

    op.execute('''\nCREATE TABLE photos (
	id UUID DEFAULT gen_random_uuid() NOT NULL, 
	file_id UUID NOT NULL, 
	latitude NUMERIC(10, 7), 
	longitude NUMERIC(10, 7), 
	captured_at TIMESTAMP WITH TIME ZONE, 
	device_info VARCHAR, 
	linked_type VARCHAR(50), 
	linked_id UUID, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(file_id) REFERENCES files (id)
)\n''')

    op.execute('''CREATE INDEX idx_comments_parent ON comments (commentable_type, commentable_id, created_at)''')

    op.execute('''CREATE INDEX idx_users_org ON users (organization_id) WHERE deleted_at IS NULL''')

    op.execute('''CREATE INDEX idx_projects_org_phase ON projects (organization_id, phase) WHERE deleted_at IS NULL''')

    op.execute('''CREATE INDEX idx_assignments_project ON project_assignments (project_id, assignee_type)''')

    op.execute('''CREATE INDEX idx_assignments_assignee ON project_assignments (assignee_type, assignee_id)''')

    op.execute('''CREATE UNIQUE INDEX idx_rfis_num ON rfis (project_id, number)''')

    op.execute('''ALTER TABLE sub_companies ADD CONSTRAINT fk_sub_companies_primary_contact FOREIGN KEY(primary_contact_user_id) REFERENCES sub_users (id)''')


def downgrade() -> None:
    op.execute('ALTER TABLE sub_companies DROP CONSTRAINT IF EXISTS fk_sub_companies_primary_contact')
    op.drop_table('photos')
    op.drop_table('drawing_sheets')
    op.drop_table('documents')
    op.drop_table('bid_submissions')
    op.drop_table('transmittals')
    op.drop_table('todos')
    op.drop_table('submittals')
    op.drop_table('schedule_tasks')
    op.drop_table('rfis')
    op.drop_table('punch_list_items')
    op.drop_table('project_assignments')
    op.drop_table('procurement_items')
    op.drop_table('pay_apps')
    op.drop_table('owner_portal_configs')
    op.drop_table('meetings')
    op.drop_table('inspections')
    op.drop_table('files')
    op.drop_table('event_logs')
    op.drop_table('drawings')
    op.drop_table('daily_logs')
    op.drop_table('change_orders')
    op.drop_table('budget_line_items')
    op.drop_table('bid_packages')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('sub_users')
    op.drop_table('owner_users')
    op.drop_table('invitations')
    op.drop_table('integration_connections')
    op.drop_table('inspection_templates')
    op.drop_table('cost_code_templates')
    op.drop_table('contacts')
    op.drop_table('comments')
    op.drop_table('audit_logs')
    op.drop_table('sub_companies')
    op.drop_table('owner_accounts')
    op.drop_table('organizations')
    op.drop_table('notifications')
