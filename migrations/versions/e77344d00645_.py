"""empty message

Revision ID: e77344d00645
Revises: 0f73504ba6bb
Create Date: 2025-05-08 18:33:48.480005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e77344d00645'
down_revision = '0f73504ba6bb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_search_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('country_name', sa.String(length=100), nullable=True),
    sa.Column('query', sa.String(length=256), nullable=True),
    sa.Column('result_type', sa.String(length=50), nullable=True),
    sa.Column('extra_info', sa.String(length=256), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('country_history')
    op.drop_table('search_history')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('search_history',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('query', sa.VARCHAR(length=256), nullable=True),
    sa.Column('result_type', sa.VARCHAR(length=50), nullable=True),
    sa.Column('timestamp', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('country_history',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('country_name', sa.VARCHAR(length=100), nullable=True),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('viewed_at', sa.DATETIME(), nullable=True),
    sa.Column('search_type', sa.VARCHAR(length=50), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('user_search_history')
    # ### end Alembic commands ###
