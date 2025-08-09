from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["academicworld"]

faculty_col = db["faculty"]
pub_col = db["publications"]
favorites_col = db["favorites"]
profiles_col = db["user_profiles"]



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



def save_to_favorites(user, faculty_id):
    if not favorites_col.find_one({"user": user, "faculty_id": faculty_id}):
        favorites_col.insert_one({
            "user": user,
            "faculty_id": faculty_id,
            "timestamp": datetime.utcnow()
        })

def get_favorites(user):
    return list(favorites_col.find({"user": user}))

def remove_from_favorites(user, faculty_id):
    favorites_col.delete_one({"user": user, "faculty_id": faculty_id})

def clear_favorites(user):
    favorites_col.delete_many({"user": user})


def save_user_profile(user, first_name, last_name, email):
    profiles_col.update_one(
        {"user": user},
        {"$set": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email
        }},
        upsert=True
    )

def get_user_profile(user):
    return profiles_col.find_one({"user": user}) or {}

def save_user_interests(user, interests):
    profiles_col.update_one(
        {"user": user},
        {"$set": {"interests": interests}},
        upsert=True
    )

def get_user_interests(user):
    profile = get_user_profile(user)
    return profile.get("interests", [])

def add_favorite_to_profile(user, faculty_id):
    profiles_col.update_one(
        {"user": user},
        {"$addToSet": {"favorites": faculty_id}},
        upsert=True
    )

def remove_favorite_from_profile(user, faculty_id):
    profiles_col.update_one(
        {"user": user},
        {"$pull": {"favorites": faculty_id}}
    )
