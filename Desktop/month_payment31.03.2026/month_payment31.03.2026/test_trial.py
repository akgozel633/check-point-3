#!/usr/bin/env python3

from app import app
from models import User
from database import db

with app.app_context():
    # Get all users and check their trial status
    users = User.query.all()
    print(f"Found {len(users)} users:")
    
    for user in users:
        print(f"\nUser: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Created: {user.created_at}")
        print(f"  Has trial: {user.has_trial}")
        print(f"  Trial start: {user.trial_start}")
        print(f"  Trial end: {user.trial_end}")
        print(f"  Is trial active: {user.is_trial_active()}")
        print(f"  Days remaining: {user.trial_days_remaining()}")
        print(f"  Needs payment for selling: {user.needs_payment_for_selling()}")
        print("-" * 50)
