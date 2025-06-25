"""initial_schema

Revision ID: 324bd1152169
Revises: 
Create Date: 2025-06-04 18:53:07.816356

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "324bd1152169"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user table first
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    # Create accesstoken table
    op.create_table(
        "accesstoken",
        sa.Column("token", sa.String(length=43), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index(
        op.f("ix_accesstoken_user_id"), "accesstoken", ["user_id"], unique=False
    )

    # Create maintenance_item table
    op.create_table(
        "maintenance_item",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("default_interval", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create vehicle table
    op.create_table(
        "vehicle",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("brand", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=50), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("odometer", sa.Integer(), nullable=False),
        sa.Column("photo", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create user_maintenance_item table
    op.create_table(
        "user_maintenance_item",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("custom_interval", sa.Integer(), nullable=True),
        sa.Column("last_service_odometer", sa.Integer(), nullable=True),
        sa.Column("last_service_date", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["maintenance_item.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["vehicle_id"],
            ["vehicle.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create service_record table
    op.create_table(
        "service_record",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.func.gen_random_uuid()),
        sa.Column("user_item_id", sa.Uuid(), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("service_odometer", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("service_photo", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_item_id"],
            ["user_maintenance_item.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("service_record")
    op.drop_table("user_maintenance_item")
    op.drop_table("vehicle")
    op.drop_table("maintenance_item")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_accesstoken_user_id"), table_name="accesstoken")
    op.drop_table("accesstoken")
