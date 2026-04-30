#!/usr/bin/env python3
"""Quick script to check market sync and alignment status."""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "api"))

from utils import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

# Check markets
cur.execute('SELECT COUNT(*) as total, platform, status FROM markets GROUP BY platform, status')
print('=== MARKETS SYNCED ===')
for row in cur.fetchall():
    print(f'{row[1]} ({row[2]}): {row[0]} markets')

# Check alignments
cur.execute('SELECT COUNT(*) FROM thesis_market_alignments')
alignments = cur.fetchone()[0]
print(f'\n=== ALIGNMENTS COMPUTED ===')
print(f'Total alignments: {alignments}')

# Sample markets
cur.execute('SELECT title, category FROM markets LIMIT 5')
print(f'\n=== SAMPLE MARKETS ===')
for row in cur.fetchall():
    print(f'- {row[0][:60]}... ({row[1]})')

# Check if alignment is still running
if alignments == 0:
    print('\n⏳ Alignment computation still in progress...')
else:
    # Show sample alignments
    cur.execute('''
        SELECT t.title, m.title, tma.alignment_score, tma.alignment_direction
        FROM thesis_market_alignments tma
        JOIN theses t ON tma.thesis_id = t.id
        JOIN markets m ON tma.market_id = m.id
        ORDER BY tma.alignment_score DESC
        LIMIT 5
    ''')
    print(f'\n=== TOP ALIGNMENTS ===')
    for row in cur.fetchall():
        print(f'- {row[0][:30]} → {row[1][:40]} (score: {row[2]}, {row[3]})')

cur.close()
conn.close()
