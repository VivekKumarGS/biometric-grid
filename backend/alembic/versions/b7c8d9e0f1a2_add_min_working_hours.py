
"""Add settings.min_working_hours."""

from alembic import op
import sqlalchemy as sa

revision = "b7c8d9e0f1a2"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "settings" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("settings")
    }

    if "min_working_hours" not in columns:
        op.add_column(
            "settings",
            sa.Column(
                "min_working_hours",
                sa.Float(),
                nullable=False,
                server_default="9.0",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "settings" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("settings")
    }

    if "min_working_hours" in columns:
        op.drop_column("settings", "min_working_hours")
