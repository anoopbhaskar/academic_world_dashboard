from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["academicworld"]

faculty_col = db["faculty"]
pub_col = db["publications"]
# Removed separate favorites collection so everything goes in user_profile now
user_profile_col = db["user_profile"]  # Single collection for all user data

def get_all_universities():
    return sorted(faculty_col.distinct("affiliation.name"))

def get_faculty_by_university(univ_name):
    return list(faculty_col.find({"affiliation.name": univ_name}))

def get_all_faculty_names():
    return sorted([f["name"] for f in faculty_col.find({}, {"name": 1})])

def get_faculty_by_name(name):
    return faculty_col.find_one({"name": name})

def get_faculty_by_id(fid):
    return faculty_col.find_one({"id": fid})

def get_publications_by_ids(pub_ids, limit=5):
    return list(pub_col.find({"id": {"$in": pub_ids}}).sort("numCitations", -1).limit(limit))

def get_publication_counts_by_keyword(keyword, start_year):
    pipeline = [
        {"$match": {
            "keywords.name": keyword,
            "year": {"$gte": start_year}
        }},
        {"$group": {
            "_id": "$year",
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    results = list(pub_col.aggregate(pipeline))

    years = list(range(start_year, 2025))
    year_counts = {r["_id"]: r["count"] for r in results}
    return [year_counts.get(year, 0) for year in years], years

# update the user profile functions so that everything in one collection now

def create_or_update_user_profile(user_email, first_name=None, last_name=None):
    """Create or update basic user profile information"""
    update_data = {
        "email": user_email,
        "last_updated": datetime.utcnow()
    }
    
    if first_name:
        update_data["first_name"] = first_name
    if last_name:
        update_data["last_name"] = last_name
    
    user_profile_col.update_one(
        {"email": user_email},
        {
            "$set": update_data,
            "$setOnInsert": {
                "interests": [],
                "favorite_faculty": [],
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )

def get_user_profile(user_email):
    """Get complete user profile"""
    profile = user_profile_col.find_one({"email": user_email})
    if not profile:
        create_or_update_user_profile(user_email)
        profile = user_profile_col.find_one({"email": user_email})
    return profile

def save_user_interests(user, interests):
    """Save user's research interests to their profile"""
    user_email = user.get("email") if isinstance(user, dict) else user
    
    user_profile_col.update_one(
        {"email": user_email},
        {
            "$set": {
                "interests": interests,
                "last_updated": datetime.utcnow()
            }
        },
        upsert=True
    )

def get_user_interests(user):
    """Get user's research interests from their profile"""
    user_email = user.get("email") if isinstance(user, dict) else user
    profile = get_user_profile(user_email)
    return profile.get("interests", [])

def add_user_interest(user, interest):
    """Add a single interest to user's profile"""
    user_email = user.get("email") if isinstance(user, dict) else user
    
    user_profile_col.update_one(
        {"email": user_email},
        {
            "$addToSet": {"interests": interest},
            "$set": {"last_updated": datetime.utcnow()}
        },
        upsert=True
    )

def remove_user_interest(user, interest):
    """Remove a single interest from user's profile"""
    user_email = user.get("email") if isinstance(user, dict) else user
    
    user_profile_col.update_one(
        {"email": user_email},
        {
            "$pull": {"interests": interest},
            "$set": {"last_updated": datetime.utcnow()}
        }
    )

def save_to_favorites(user_email, faculty_id):
    """Add a faculty member to user's favorites with both ID and name"""
    faculty = get_faculty_by_id(faculty_id)
    if not faculty:
        return False 
    
    profile = get_user_profile(user_email)
    current_favorites = profile.get("favorite_faculty", [])
    
    existing_favorite = any(
        fav.get("id") == faculty_id if isinstance(fav, dict) else fav == faculty_id 
        for fav in current_favorites
    )
    
    if not existing_favorite:
        favorite_obj = {
            "id": faculty_id,
            "name": faculty["name"],
            "university": faculty.get("affiliation", {}).get("name", "Unknown University"),
            "added_at": datetime.utcnow()
        }
        
        user_profile_col.update_one(
            {"email": user_email},
            {
                "$addToSet": {"favorite_faculty": favorite_obj},
                "$set": {"last_updated": datetime.utcnow()}
            },
            upsert=True
        )
        return True  
    return False  

def get_favorites(user_email):
    """Get user's favorite faculty members"""
    profile = get_user_profile(user_email)
    favorite_faculty = profile.get("favorite_faculty", [])
    
    formatted_favorites = []
    for fav in favorite_faculty:
        if isinstance(fav, dict):
            formatted_favorites.append({
                "faculty_id": fav["id"],
                "name": fav["name"],
                "university": fav.get("university", "Unknown"),
                "added_at": fav.get("added_at")
            })
    return formatted_favorites

def remove_from_favorites(user_email, faculty_id):
    """Remove a faculty member from user's favorites (handles both old and new format)"""
    user_profile_col.update_one(
        {"email": user_email},
        {
            "$pull": {
                "favorite_faculty": {"$or": [
                    {"id": faculty_id}
                ]}
            },
            "$set": {"last_updated": datetime.utcnow()}
        }
    )

def clear_favorites(user_email):
    """Clear all favorites for a user"""
    user_profile_col.update_one(
        {"email": user_email},
        {
            "$set": {
                "favorite_faculty": [],
                "last_updated": datetime.utcnow()
            }
        }
    )


def clear_user_profile(user_email):
    """Completely remove a user's profile (for testing/cleanup)"""
    user_profile_col.delete_one({"email": user_email})

def get_user_stats(user_email):
    """Get summary statistics for a user"""
    profile = get_user_profile(user_email)
    return {
        "total_interests": len(profile.get("interests", [])),
        "total_favorites": len(profile.get("favorite_faculty", [])),
        "created_at": profile.get("created_at"),
        "last_updated": profile.get("last_updated")
    }

def save_user_profile(user, first_name, last_name, email):
    """Legacy function - now uses unified profile system"""
    create_or_update_user_profile(email, first_name, last_name)

def add_favorite_to_profile(user, faculty_id):
    """Legacy function - now uses unified profile system"""
    user_email = user.get("email") if isinstance(user, dict) else user
    save_to_favorites(user_email, faculty_id)

def remove_favorite_from_profile(user, faculty_id):
    """Legacy function - now uses unified profile system"""
    user_email = user.get("email") if isinstance(user, dict) else user
    remove_from_favorites(user_email, faculty_id)
