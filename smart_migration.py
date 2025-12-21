import os
import re
from datetime import datetime

ALEMBIC_DIR = "alembic/versions"

def generate_migration():
    if not os.path.exists(ALEMBIC_DIR):
        print(f"Directory {ALEMBIC_DIR} not found.")
        return

    # Find the latest migration file
    files = [f for f in os.listdir(ALEMBIC_DIR) if f.endswith(".py")]
    latest_file = None
    latest_rev = None
    
    # Heuristic: Sort by filename since often they are prefixed with revision or date.
    # However, standard Alembic files are <rev>_<slug>.py. The timestamp-based ones are usually sorted.
    # Let's try to extract the revision ID from the content of each file to be sure.
    
    rev_map = {} # rev -> down_rev
    
    for f in files:
        with open(os.path.join(ALEMBIC_DIR, f), 'r') as content:
            txt = content.read()
            rev_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", txt)
            down_match = re.search(r"down_revision\s*=\s*['\"]([^'\"]+)['\"]", txt)
            
            if rev_match:
                rev = rev_match.group(1)
                down = down_match.group(1) if down_match else None
                rev_map[rev] = down

    # Identify head: The revision that appears as a key but NEVER as a value (down_revision)
    all_revs = set(rev_map.keys())
    all_downs = set(filter(None, rev_map.values()))
    heads = list(all_revs - all_downs)
    
    if not heads:
        print("Could not determine head revision.")
        latest_rev = None
    elif len(heads) > 1:
        print(f"Multiple heads found: {heads}. Picking one arbitrarily.")
        latest_rev = heads[0]
    else:
        latest_rev = heads[0]
        print(f"Found head revision: {latest_rev}")

    # Generate new file
    new_rev_id = datetime.now().strftime("%Y%m%d%H%M")
    filename = f"{new_rev_id}_add_decumulation_enabled.py"
    filepath = os.path.join(ALEMBIC_DIR, filename)
    
    down_rev_str = f"'{latest_rev}'" if latest_rev else "None"
    
    content = f"""\"\"\"add decumulation enabled column

Revision ID: {new_rev_id}
Revises: {latest_rev if latest_rev else ''}
Create Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

\"\"\"
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '{new_rev_id}'
down_revision = {down_rev_str}
branch_labels = None
depends_on = None

def upgrade():
    # Helper to check if column exists before adding (Idempotency)
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('decumulation_strategies')]
    
    if 'enabled' not in columns:
        op.add_column('decumulation_strategies', sa.Column('enabled', sa.Boolean(), server_default='1', nullable=True))

def downgrade():
    with op.batch_alter_table('decumulation_strategies') as batch_op:
        batch_op.drop_column('enabled')
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"Generated migration file: {filepath}")

if __name__ == "__main__":
    generate_migration()
