import sys
import glob

def refactor():
    for path in glob.glob('src/database/*.py'):
        if path.endswith('__init__.py') or path.endswith('client.py'):
            continue
            
        with open(path, 'r') as f:
            content = f.read()

        if 'supabase.table' not in content:
            continue
            
        # Ensure import asyncio
        if 'import asyncio' not in content:
            if 'from __future__ import annotations' in content:
                content = content.replace("from __future__ import annotations", "from __future__ import annotations\nimport asyncio")
            elif 'import logging' in content:
                content = content.replace("import logging", "import asyncio\nimport logging")
                
        # Find all `execute()` calls that belong to supabase queries.
        # It's always called at the end of a chain.
        # We can just replace `.execute()` with `.execute` and prepend it with `await asyncio.to_thread( ... )`? 
        # But `await asyncio.to_thread` requires the callable, plus it requires the whole chain to be inside it?
        # Actually `await asyncio.to_thread(lambda: supabase.table(...).execute())`
        pass
