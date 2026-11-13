"""One-time CLI creation of first organization and admin; never exposed as HTTP endpoint."""
import argparse, getpass
from sqlalchemy import select
from .store import init_db, Session, Organization, User, new_id
from .auth import PH

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--organization',required=True)
    parser.add_argument('--email',required=True)
    args=parser.parse_args()
    pwd=getpass.getpass('Mot de passe administrateur (12 caractères minimum) : ')
    if len(pwd)<12:raise SystemExit('Mot de passe trop court')
    init_db()
    with Session.begin() as db:
        if db.scalar(select(User).where(User.email==args.email.strip().lower())):raise SystemExit('Email déjà utilisé')
        oid=new_id();db.add(Organization(id=oid,name=args.organization.strip()))
        db.add(User(id=new_id(),organization_id=oid,email=args.email.strip().lower(),password_hash=PH.hash(pwd),role='admin'))
    print('Compte administrateur créé.')
if __name__=='__main__':main()
