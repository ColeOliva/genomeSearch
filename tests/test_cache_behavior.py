import os
import time
from app import app, cache, db_mtime, DATABASE


def make_cache_key(query, page=1, per_page=50, species='', chromosome='', constraint='', clinical='', gene_type='', go_category=''):
    return f"search:{db_mtime()}:{query}:{species}:{chromosome}:{constraint}:{clinical}:{gene_type}:{go_category}:{page}:{per_page}"


def test_cache_and_touch_invalidation(tmp_path, monkeypatch):
    client = app.test_client()
    query = 'BRCA1'

    # Ensure no pre-existing cache for this key
    key1 = make_cache_key(query)
    cache.delete(key1)

    # First request should populate cache
    r1 = client.get(f'/search?q={query}')
    assert r1.status_code == 200
    assert cache.get(key1) is not None

    # Touch DB to change mtime
    old_mtime = db_mtime()
    os.utime(DATABASE, None)
    time.sleep(0.01)
    new_mtime = db_mtime()
    assert new_mtime >= old_mtime

    key2 = make_cache_key(query)
    # keys should differ after mtime change
    assert key1 != key2

    # After touching DB, making request should populate new key
    r2 = client.get(f'/search?q={query}')
    assert r2.status_code == 200
    assert cache.get(key2) is not None


def test_admin_clear_cache_requires_token(monkeypatch):
    client = app.test_client()
    query = 'TP53'
    key = make_cache_key(query)
    cache.set(key, {'results': []})
    assert cache.get(key) is not None

    # No token set in env: should allow clearing
    if 'ADMIN_CLEAR_TOKEN' in os.environ:
        monkeypatch.delenv('ADMIN_CLEAR_TOKEN', raising=False)

    r = client.post('/_admin/clear_cache')
    assert r.status_code == 200
    assert cache.get(key) is None

    # Now set token and require it
    monkeypatch.setenv('ADMIN_CLEAR_TOKEN', 'secret')
    cache.set(key, {'results': []})
    r_fail = client.post('/_admin/clear_cache')
    assert r_fail.status_code == 401

    # Provide token in header
    r_ok = client.post('/_admin/clear_cache', headers={'X-Admin-Token': 'secret'})
    assert r_ok.status_code == 200
    assert cache.get(key) is None
