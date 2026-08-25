"""add unit_price and transaction_date to sales_items

Revision ID: 98651b252ec1
Revises: d60ebee339bf
Create Date: 2026-08-13 00:00:00.000000

Alasan migrasi ini:
csv_parser.py (Jay) mewajibkan REQUIRED_COLUMNS termasuk `unit_price` dan
`transaction_date`, tapi tabel sales_items sebelumnya cuma punya
product_name/category/qty_sold/remaining_stock. Tanpa migrasi ini, data
harga (dibutuhkan buat narasi "Dead-Stock Rescue" -- hitung margin) akan
hilang begitu saja tiap kali analyze.py insert ke database.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '98651b252ec1'
down_revision: Union[str, Sequence[str], None] = 'd60ebee339bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sales_items', sa.Column('transaction_date', sa.Date(), nullable=True))
    op.add_column('sales_items', sa.Column('unit_price', sa.Float(), nullable=True))
    # qty_sold/remaining_stock dilonggarkan jadi nullable -- csv_parser.py bisa
    # saja tetap simpan baris dengan nilai rusak (NULL) untuk keperluan audit,
    # correlation_engine.py yang nanti memfilternya, bukan constraint DB.
    op.alter_column('sales_items', 'qty_sold', existing_type=sa.Integer(), nullable=True)
    op.alter_column('sales_items', 'remaining_stock', existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('sales_items', 'remaining_stock', existing_type=sa.Integer(), nullable=False)
    op.alter_column('sales_items', 'qty_sold', existing_type=sa.Integer(), nullable=False)
    op.drop_column('sales_items', 'unit_price')
    op.drop_column('sales_items', 'transaction_date')
