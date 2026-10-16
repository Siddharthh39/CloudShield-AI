from schemas import Profile
from database import db_profile

def create_profile(profile: Profile) -> Profile:
    global db_profile
    db_profile = profile
    return db_profile

def get_profile() -> Profile | None:
    return db_profile

def update_profile(updated_profile: Profile) -> Profile | None:
    global db_profile
    if db_profile is None:
        return None
    db_profile = updated_profile
    return db_profile

