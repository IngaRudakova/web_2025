from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_reviews_table'
down_revision = 'previous_revision_id'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('course_id', sa.Integer, sa.ForeignKey('courses.id')),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
    )
    data_upgrades()

def downgrade():
    op.drop_table('reviews')

def data_upgrades():
    """Add any optional data upgrade migrations here!"""
    table = sa.sql.table('categories', sa.sql.column('name', sa.String))
    op.bulk_insert(table, [
        {'name': 'Программирование'},
        {'name': 'Математика'},
        {'name': 'Языкознание'},
    ])
