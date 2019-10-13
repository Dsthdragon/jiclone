"""Added Category, Ad, Region, Place

Revision ID: 7ba1383477a6
Revises: ed20d061cb4f
Create Date: 2019-08-22 16:34:07.474574

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '7ba1383477a6'
down_revision = 'ed20d061cb4f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ad_image', sa.Column('ad_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'ad_image', 'ad', ['ad_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'ad_image', type_='foreignkey')
    op.drop_column('ad_image', 'ad_id')
    # ### end Alembic commands ###
