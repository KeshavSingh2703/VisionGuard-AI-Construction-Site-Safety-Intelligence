from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_safety_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_type", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("stored_path", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "safety_violations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploads.id", ondelete="CASCADE")),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("violation_type", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("frame_number", sa.Integer()),
        sa.Column("description", sa.Text()),
        sa.Column("detected_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "proximity_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploads.id", ondelete="CASCADE")),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("worker_id", sa.Text()),
        sa.Column("machine_type", sa.Text(), nullable=False),
        sa.Column("distance_px", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("frame_number", sa.Integer()),
        sa.Column("detected_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "site_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploads.id", ondelete="CASCADE")),
        sa.Column("total_files", sa.Integer(), nullable=False),
        sa.Column("total_frames", sa.Integer()),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("ppe_violations", sa.Integer(), nullable=False),
        sa.Column("zone_violations", sa.Integer(), nullable=False),
        sa.Column("proximity_violations", sa.Integer(), nullable=False),
        sa.Column("time_based_violations", sa.Integer(), nullable=False),
        sa.Column("pipeline_status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("site_metrics")
    op.drop_table("proximity_events")
    op.drop_table("safety_violations")
    op.drop_table("uploads")
