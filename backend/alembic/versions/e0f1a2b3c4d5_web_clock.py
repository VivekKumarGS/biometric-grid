
"""Web sign-in clock.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4

Employees can sign in and out from the browser as well as at a
fingerprint scanner. Both kinds of punch go into attendance_logs.

Downgrade deletes web punches first because they have no finger_id.
"""

from alembic import op
import sqlalchemy as sa

revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Safe to rerun against schemas where earlier migrations already
    # made these changes.
    op.execute(
        "ALTER TABLE attendance_logs "
        "ALTER COLUMN finger_id DROP NOT NULL"
    )

    op.execute(
        """
        ALTER TABLE attendance_logs
        ADD COLUMN IF NOT EXISTS source
        VARCHAR(16) NOT NULL DEFAULT 'device'
        """
    )

    op.execute(
        """
        ALTER TABLE attendance_logs
        ADD COLUMN IF NOT EXISTS source_ip VARCHAR(64)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_attendance_user_time
        ON attendance_logs (tenant_id, user_id, timestamp)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_attendance_user_time")

    # Web punches cannot survive restoring finger_id to NOT NULL.
    op.execute("DELETE FROM attendance_logs WHERE finger_id IS NULL")

    op.execute(
        "ALTER TABLE attendance_logs DROP COLUMN IF EXISTS source_ip"
    )
    op.execute(
        "ALTER TABLE attendance_logs DROP COLUMN IF EXISTS source"
    )

    op.execute(
        "ALTER TABLE attendance_logs "
        "ALTER COLUMN finger_id SET NOT NULL"
    )
