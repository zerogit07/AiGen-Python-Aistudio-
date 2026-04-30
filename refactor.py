import os
import glob

def refactor():
    for path in glob.glob('src/database/*.py'):
        if path.endswith('__init__.py') or path.endswith('client.py'):
            continue
            
        with open(path, 'r') as f:
            content = f.read()

        if 'supabase.table' not in content:
            continue
            
        # Replace
        content = content.replace("supabase.table", "await supabase.table")
        
        with open(path, 'w') as f:
            f.write(content)

if __name__ == '__main__':
    refactor()
