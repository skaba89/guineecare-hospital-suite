"""PostgreSQL integration tests for nullable facility_id RLS policies."""
from __future__ import annotations
import os, sys
from pathlib import Path
from types import SimpleNamespace
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT)) if str(BACKEND_ROOT) not in sys.path else None

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import sessionmaker
from app.core.tenant import bind_tenant_context
from app.db.session import SessionLocal
from app.modules.auth.models import DataBreach
from app.modules.facilities.models import Facility
from app.modules.notifications.models import Notification
from app.modules.user_profile.models import UserFeedback
from app.modules.users.models import User

A='10000000-0000-0000-0000-000000000001'; B='20000000-0000-0000-0000-000000000001'
UA='10000000-0000-0000-0000-000000000101'; AA='10000000-0000-0000-0000-000000000102'; UB='20000000-0000-0000-0000-000000000101'
FA='10000000-0000-0000-0000-000000000201'; FB='20000000-0000-0000-0000-000000000201'
NA='10000000-0000-0000-0000-000000000301'; NB='20000000-0000-0000-0000-000000000301'
BA='10000000-0000-0000-0000-000000000401'; BB='20000000-0000-0000-0000-000000000401'; BN='90000000-0000-0000-0000-000000000401'

def seed(url):
    e=create_engine(url); S=sessionmaker(bind=e); d=S()
    try:
        for model, ids in [(Notification,[NA,NB]),(UserFeedback,[FA,FB]),(DataBreach,[BA,BB,BN])]:
            d.query(model).filter(model.id.in_(ids)).delete(synchronize_session=False)
        d.query(User).filter(User.id.in_([UA,AA,UB])).delete(synchronize_session=False)
        d.query(Facility).filter(Facility.id.in_([A,B])).delete(synchronize_session=False); d.commit()
        d.add_all([Facility(id=A,code='RLS2-A',name='RLS2 A'),Facility(id=B,code='RLS2-B',name='RLS2 B')]); d.flush()
        d.add_all([
            User(id=UA,facility_id=A,email='rls2-a@test',password_hash='x',first_name='A',last_name='Doctor',role='DOCTOR',is_active=True),
            User(id=AA,facility_id=A,email='rls2-admin@test',password_hash='x',first_name='A',last_name='Admin',role='ADMIN',is_active=True),
            User(id=UB,facility_id=B,email='rls2-b@test',password_hash='x',first_name='B',last_name='Doctor',role='DOCTOR',is_active=True),
        ]); d.flush()
        d.add_all([
            UserFeedback(id=FA,user_id=UA,facility_id=A,category='bug',message='A feedback'),
            UserFeedback(id=FB,user_id=UB,facility_id=B,category='bug',message='B feedback'),
            Notification(id=NA,recipient_id=UA,facility_id=A,category='system',title='A notice'),
            Notification(id=NB,recipient_id=UB,facility_id=B,category='system',title='B notice'),
            DataBreach(id=BA,facility_id=A,reported_by=AA,title='A breach',description='A',severity='HIGH'),
            DataBreach(id=BB,facility_id=B,reported_by=UB,title='B breach',description='B',severity='HIGH'),
            DataBreach(id=BN,facility_id=None,reported_by=None,title='National breach',description='N',severity='CRITICAL'),
        ]); d.commit()
    finally: d.close(); e.dispose()

def ids(db, model): return {r.id for r in db.query(model).all()}

def assert_blocked(fn):
    blocked=False
    try: fn()
    except DBAPIError: blocked=True
    assert blocked

def main():
    admin=os.environ['RLS_ADMIN_DATABASE_URL']; seed(admin)
    d=SessionLocal()
    try:
        # No trusted identity: nullable protected data is fail-closed.
        assert ids(d, UserFeedback)==set(); assert ids(d, Notification)==set(); assert ids(d, DataBreach)==set()

        bind_tenant_context(d,SimpleNamespace(id=UA,role='DOCTOR',facility_id=A))
        assert ids(d,UserFeedback)=={FA}
        assert ids(d,Notification)=={NA}
        assert ids(d,DataBreach)=={BA}

        # Doctor cannot update feedback even when it is their own.
        f=d.query(UserFeedback).filter(UserFeedback.id==FA).one(); f.status='resolved'
        assert_blocked(d.commit); d.rollback()

        bind_tenant_context(d,SimpleNamespace(id=AA,role='ADMIN',facility_id=A))
        assert ids(d,UserFeedback)=={FA}
        f=d.query(UserFeedback).filter(UserFeedback.id==FA).one(); f.status='resolved'; d.commit()
        assert ids(d,Notification)==set(), 'facility admin must not read another user notification'
        assert ids(d,DataBreach)=={BA}

        bind_tenant_context(d,SimpleNamespace(id='90000000-0000-0000-0000-000000000999',role='SUPER_ADMIN',facility_id=None))
        assert ids(d,UserFeedback)=={FA,FB}
        assert ids(d,Notification)=={NA,NB}
        assert ids(d,DataBreach)=={BA,BB,BN}

        # RLS identity includes trusted database user/role values.
        row=d.execute(text("SELECT current_setting('app.current_role', true), current_setting('app.current_user_id', true)" )).one()
        assert row[0]=='SUPER_ADMIN' and row[1]
    finally: d.close()
    print('PASS: nullable facility_id RLS policies enforce user, facility and national scopes')

if __name__=='__main__': main()
