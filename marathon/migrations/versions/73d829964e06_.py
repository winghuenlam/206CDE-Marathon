"""empty message

Revision ID: 73d829964e06
Revises: 437ccdfbafc4
Create Date: 2019-11-03 12:53:20.345504

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73d829964e06'
down_revision = '437ccdfbafc4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('address', sa.String(length=20), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'address')
    # ### end Alembic commands ###
