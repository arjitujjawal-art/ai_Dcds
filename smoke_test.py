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

# Test 5: Validator
from nlp.sql_validator import validate_sql
v1 = validate_sql(n['sql'], 'student')
v2 = validate_sql('DROP TABLE students', 'admin')
print('Valid SQL   :', 'PASS' if v1['valid'] else 'FAIL', v1['reason'])
print('DROP blocked:', 'PASS' if not v2['valid'] else 'FAIL', v2['reason'])
