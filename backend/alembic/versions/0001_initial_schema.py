"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create ENUMs
    op.execute("CREATE TYPE category_enum AS ENUM ('water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other')")
    op.execute("CREATE TYPE priority_enum AS ENUM ('high', 'normal', 'low')")
    op.execute("CREATE TYPE status_enum AS ENUM ('open', 'in_progress', 'resolved', 'rejected')")

    op.create_table(
        'complaints',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('text', sa.String(length=2000), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('reporter_contact', sa.String(length=255), nullable=True),
        sa.Column('category', postgresql.ENUM('water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other', name='category_enum', create_type=False), nullable=False),
        sa.Column('priority', postgresql.ENUM('high', 'normal', 'low', name='priority_enum', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('open', 'in_progress', 'resolved', 'rejected', name='status_enum', create_type=False), server_default='open', nullable=False),
        sa.Column('ai_summary', sa.String(length=140), nullable=True),
        sa.Column('triaged_by', sa.String(length=32), nullable=True),
        sa.Column('triage_latency_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('char_length(text) >= 10', name='chk_complaint_text_length'),
        sa.CheckConstraint('char_length(location) >= 3', name='chk_complaint_location_length'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_complaints_status_priority', 'complaints', ['status', 'priority'])
    op.create_index('idx_complaints_created_at_desc', 'complaints', [sa.text('created_at DESC')])

def downgrade() -> None:
    op.drop_index('idx_complaints_created_at_desc', table_name='complaints')
    op.drop_index('idx_complaints_status_priority', table_name='complaints')
    op.drop_table('complaints')
    op.execute("DROP TYPE status_enum")
    op.execute("DROP TYPE priority_enum")
    op.execute("DROP TYPE category_enum")
