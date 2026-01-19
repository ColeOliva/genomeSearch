import json

from app import app

with app.test_client() as c:
    r = c.get('/search?q=BRCA1')
    print('status', r.status_code)
    try:
        j = r.get_json()
        print('keys:', list(j.keys()))
        print('total:', j.get('total'))
        # print first result symbol if available
        if j.get('results'):
            first = j['results'][0]
            print('first symbol:', first.get('symbol'))
    except Exception as e:
        print('failed to parse json:', e)
