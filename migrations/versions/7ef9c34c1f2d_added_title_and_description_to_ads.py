"""Added title and description to Ads

Revision ID: 7ef9c34c1f2d
Revises: 49def87e0a5a
Create Date: 2019-09-13 19:16:17.811390

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


# revision identifiers, used by Alembic.
revision = '7ef9c34c1f2d'
down_revision = '49def87e0a5a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ad', sa.Column('description', sa.Text(), nullable=False))
    op.add_column('ad', sa.Column('title', sa.String(length=255), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ad', 'title')
    op.drop_column('ad', 'description')
    # ### end Alembic commands ###
