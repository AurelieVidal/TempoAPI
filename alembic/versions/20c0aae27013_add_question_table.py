"""Add question table

Revision ID: 20c0aae27013
Revises: b6a7caadf748
Create Date: 2024-09-12 11:25:41.169382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20c0aae27013'
down_revision: Union[str, None] = 'b6a7caadf748'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('question',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('question', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('question')
                    )
    op.create_table('user_question',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('question_id', sa.Integer(), nullable=False),
                    sa.Column('response', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['question_id'], ['question.id']),
                    sa.ForeignKeyConstraint(['user_id'], ['user.id']),
                    sa.PrimaryKeyConstraint('user_id', 'question_id')
                    )
    op.add_column('user', sa.Column('devices', sa.String(), nullable=True))

    op.execute("UPDATE public.user SET devices = '[]' WHERE devices IS NULL")

    op.alter_column(
        'user', 'devices', existing_type=sa.String(), nullable=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'devices')
    op.drop_table('user_question')
    op.drop_table('question')
    # ### end Alembic commands ###