"""replace demographics and competitor_prices with ch3coo's schema

Revision ID: d60ebee339bf
Revises: a7a953e92c42
Create Date: 2026-08-12 00:00:00.000000

Alasan migrasi ini:
Skema `demographics`/`competitor_prices` sebelumnya (location_area,
population_density, dst.) dibangun untuk use case Hyper-Local Expansion,
yang sudah disepakati tim masuk roadmap, bukan MVP sekarang. Skema yang
benar-benar dipakai correlation_engine.py (ch3coo) adalah versi
category/segment_name/keywords dan category/product_name/price. Migrasi
ini mengganti tabel supaya keduanya selaras -- dan menambahkan
server_default gen_random_uuid() supaya insert lewat psycopg2 mentah
(seed_dummy_data.py) tidak crash karena id NULL.

CATATAN: down_revision awalnya '960bedd0055a', diubah ke 'a7a953e92c42'
karena migrasi itu ternyata juga anak dari 960bedd0055a -- dua migrasi
bercabang dari induk yang sama bikin Alembic punya 2 head sekaligus.
Merantai ke a7a953e92c42 aman: migrasi itu cuma alter_column tipe/komentar
pada skema LAMA, baru setelahnya migrasi ini drop total tabelnya.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd60ebee339bf'
down_revision: Union[str, Sequence[str], None] = 'a7a953e92c42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    # --- drop skema lama (location-based) ---
    op.drop_index(op.f('ix_demographics_location_area'), table_name='demographics')
    op.drop_table('demographics')
    op.drop_index(op.f('ix_competitor_prices_competitor_name'), table_name='competitor_prices')
    op.drop_table('competitor_prices')

    # --- buat ulang dengan skema ch3coo ---
    op.create_table(
        'demographics',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('segment_name', sa.Text(), nullable=False),
        sa.Column('keywords', sa.Text(), nullable=False),
        sa.Column('age_group', sa.String(length=50), nullable=True),
        sa.Column('source', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_demographics_category'), 'demographics', ['category'], unique=False)

    op.create_table(
        'competitor_prices',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('product_name', sa.Text(), nullable=False),
        sa.Column('competitor_name', sa.Text(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False),
        sa.CheckConstraint('price > 0', name='ck_competitor_prices_price_positive'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_competitor_prices_category'), 'competitor_prices', ['category'], unique=False)


def downgrade() -> None:
    """Downgrade schema -- kembali ke skema location-based Danish."""
    op.drop_index(op.f('ix_competitor_prices_category'), table_name='competitor_prices')
    op.drop_table('competitor_prices')
    op.drop_index(op.f('ix_demographics_category'), table_name='demographics')
    op.drop_table('demographics')

    op.create_table(
        'competitor_prices',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('competitor_name', sa.String(length=100), nullable=True),
        sa.Column('product_category', sa.String(length=100), nullable=True),
        sa.Column('average_price', sa.Float(), nullable=True, comment='Harga rata-rata produk kompetitor (IDR)'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_competitor_prices_competitor_name'), 'competitor_prices', ['competitor_name'], unique=False)

    op.create_table(
        'demographics',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('location_area', sa.String(length=100), nullable=True),
        sa.Column('population_density', sa.Integer(), nullable=True, comment='Kepadatan per km persegi'),
        sa.Column('dominant_age_group', sa.String(length=50), nullable=True),
        sa.Column('average_income', sa.Float(), nullable=True, comment='Rata-rata pendapatan (IDR)'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_demographics_location_area'), 'demographics', ['location_area'], unique=False)