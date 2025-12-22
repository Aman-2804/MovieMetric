"""create_movies_table

Revision ID: 17fce6f22a72
Revises: 
Create Date: 2025-12-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17fce6f22a72'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('movies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('overview', sa.Text(), nullable=True),
    sa.Column('release_date', sa.Date(), nullable=True),
    sa.Column('genre', sa.String(), nullable=True),
    sa.Column('genres', sa.JSON(), nullable=True),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('vote_count', sa.Integer(), server_default='0', nullable=True),
    sa.Column('popularity', sa.Float(), nullable=True),
    sa.Column('poster_path', sa.String(), nullable=True),
    sa.Column('backdrop_path', sa.String(), nullable=True),
    sa.Column('runtime', sa.Integer(), nullable=True),
    sa.Column('budget', sa.BigInteger(), nullable=True),
    sa.Column('revenue', sa.BigInteger(), nullable=True),
    sa.Column('tagline', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('is_trending', sa.Boolean(), server_default='false', nullable=True),
    sa.Column('is_underrated', sa.Boolean(), server_default='false', nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_movies_id'), 'movies', ['id'], unique=False)
    op.create_index(op.f('ix_movies_title'), 'movies', ['title'], unique=False)
    op.create_index(op.f('ix_movies_release_date'), 'movies', ['release_date'], unique=False)
    op.create_index(op.f('ix_movies_genre'), 'movies', ['genre'], unique=False)
    op.create_index(op.f('ix_movies_rating'), 'movies', ['rating'], unique=False)
    op.create_index(op.f('ix_movies_popularity'), 'movies', ['popularity'], unique=False)
    op.create_index(op.f('ix_movies_is_trending'), 'movies', ['is_trending'], unique=False)
    op.create_index(op.f('ix_movies_is_underrated'), 'movies', ['is_underrated'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_movies_is_underrated'), table_name='movies')
    op.drop_index(op.f('ix_movies_is_trending'), table_name='movies')
    op.drop_index(op.f('ix_movies_popularity'), table_name='movies')
    op.drop_index(op.f('ix_movies_rating'), table_name='movies')
    op.drop_index(op.f('ix_movies_genre'), table_name='movies')
    op.drop_index(op.f('ix_movies_release_date'), table_name='movies')
    op.drop_index(op.f('ix_movies_title'), table_name='movies')
    op.drop_index(op.f('ix_movies_id'), table_name='movies')
    op.drop_table('movies')
