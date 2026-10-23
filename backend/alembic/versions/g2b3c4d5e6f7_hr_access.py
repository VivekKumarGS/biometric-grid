"""HR access.

Revision ID: g2b3c4d5e6f7
Revises: f1a2b3c4d5e6

Adds HR access on top of a user's existing role.
"""

from alembic import op
import sqlalchemy as sa

revision = "g2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None

HR_PERMISSIONS = (
    "payroll.view",
    "payroll.manage",
    "payroll.approve",
    "reimbursement.approve",
)


def upgrade() -> None:
    # The earlier schema-sync migration may already have added this column.
    # Preserve existing values and normalize its database constraints.
    op.execute(
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS is_hr BOOLEAN NOT NULL DEFAULT FALSE
        """
    )

    op.execute(
        """
        UPDATE users
        SET is_hr = FALSE
        WHERE is_hr IS NULL
        """
    )

    op.execute(
        """
        ALTER TABLE users
        ALTER COLUMN is_hr SET DEFAULT FALSE,
        ALTER COLUMN is_hr SET NOT NULL
        """
    )

    conn = op.get_bind()

    # Create the system HR role only if it doesn't already exist.
    exists = conn.execute(
        sa.text(
            """
            SELECT id
            FROM roles
            WHERE code = 'hr' AND tenant_id IS NULL
            """
        )
    ).first()

    if not exists:
        conn.execute(
            sa.text(
                """
                INSERT INTO roles (
                    tenant_id,
                    code,
                    name,
                    description,
                    is_system,
                    grants_all
                )
                VALUES (
                    NULL,
                    'hr',
                    'HR',
                    'Runs payroll and decides expense claims for the organisation.',
                    TRUE,
                    FALSE
                )
                """
            )
        )

    # Grant the HR role its required permissions.
    for perm in HR_PERMISSIONS:
        conn.execute(
            sa.text(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id
                FROM roles r
                CROSS JOIN permissions p
                WHERE r.code = 'hr'
                  AND r.tenant_id IS NULL
                  AND p.code = :permission
                ON CONFLICT DO NOTHING
                """
            ),
            {"permission": perm},
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Remove assignments and grants belonging to the system HR role.
    conn.execute(
        sa.text(
            """
            DELETE FROM role_permissions
            WHERE role_id IN (
                SELECT id
                FROM roles
                WHERE code = 'hr' AND tenant_id IS NULL
            )
            """
        )
    )

    conn.execute(
        sa.text(
            """
            DELETE FROM user_roles
            WHERE role_id IN (
                SELECT id
                FROM roles
                WHERE code = 'hr' AND tenant_id IS NULL
            )
            """
        )
    )

    conn.execute(
        sa.text(
            """
            DELETE FROM roles
            WHERE code = 'hr' AND tenant_id IS NULL
            """
        )
    )

    # Deliberately retain users.is_hr because it may have existed before
    # this revision through the earlier schema-sync migration.