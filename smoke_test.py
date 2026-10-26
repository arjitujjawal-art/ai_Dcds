import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import get_user, execute_query

# Test 1: Login
u = get_user('admin', 'admin123')
print('Login test  :', 'PASS' if u and u.get('role') == 'admin' else 'FAIL', u)

# Test 2: Bad login
u2 = get_user('admin', 'wrongpassword')
print('Bad login   :', 'PASS (None)' if u2 is None else 'FAIL')

# Test 3: Query
r = execute_query('SELECT name, division FROM students LIMIT 3')
print('Query test  :', 'PASS' if r['rows'] else 'FAIL', r['rows'])

# Test 4: NLP
from nlp.sql_generator import generate_sql
n = generate_sql('Show top 5 students by average marks')
print('NLP matched :', 'PASS' if n['matched'] else 'FAIL')
print('SQL snippet :', n['sql'][:100])

# Test 5: AST Governance & RBAC Validator
from nlp.sql_validator import validate_sql
v1 = validate_sql(n['sql'], 'student')
v2 = validate_sql('DROP TABLE students', 'admin')
v3 = validate_sql('SELECT * FROM app_users', 'student')
print('Valid SQL   :', 'PASS' if v1['valid'] else 'FAIL', v1['reason'])
print('DROP blocked:', 'PASS' if not v2['valid'] else 'FAIL', v2['reason'])
print('RBAC blocked:', 'PASS' if not v3['valid'] else 'FAIL', v3['reason'])

# Test 6: Deterministic AST Limit Injection
v4 = validate_sql('SELECT name, division FROM students', 'student', row_ceiling=25)
print('Limit inject:', 'PASS' if 'LIMIT 25' in (v4.get('sanitized_sql') or '') else 'FAIL', v4.get('sanitized_sql'))

# Test 7: Tabular-to-Verbal Synthesis (DataToSpeechNarrator)
from nlp.speech_narrator import DataToSpeechNarrator
summary = DataToSpeechNarrator.construct_verbal_summary(
    'Show top 3 students by marks',
    ['name', 'marks'],
    [{'name': 'Aarav Sharma', 'marks': 96.5}, {'name': 'Priya Patel', 'marks': 94.0}]
)
print('Verbal synth:', 'PASS' if 'Aarav Sharma' in summary else 'FAIL', summary)

# Test 8: Zero-Cost Neural Text-to-Speech (edge-tts)
import asyncio, edge_tts
async def test_tts():
    comm = edge_tts.Communicate("Query completed successfully.", "en-US-ChristopherNeural")
    buf = bytearray()
    async for chunk in comm.stream():
        if chunk["type"] == "audio":
            buf.extend(chunk["data"])
    return len(buf)

try:
    audio_size = asyncio.run(test_tts())
    print('Neural TTS  :', 'PASS' if audio_size > 0 else 'FAIL', f'({audio_size} bytes)')
except Exception as e:
    print('Neural TTS  : SKIPPED/OFFLINE', e)
