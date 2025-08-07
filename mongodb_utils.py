from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["academicworld"]
faculty_col = db["faculty"]
pub_col = db["publications"]

def get_all_universities():
    return sorted(faculty_col.distinct("affiliation.name"))

def get_faculty_by_university(univ_name):
    return list(faculty_col.find({"affiliation.name": univ_name}))

def get_all_faculty_names():
    return sorted([f["name"] for f in faculty_col.find({}, {"name": 1})])

def get_faculty_by_name(name):
    return faculty_col.find_one({"name": name})

def get_publications_by_ids(pub_ids, limit=5):
    return list(pub_col.find({"id": {"$in": pub_ids}}).sort("numCitations", -1).limit(limit))


from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["academicworld"]
favorites_col = db["favorites"]

def save_to_favorites(user, faculty_id):
    if not favorites_col.find_one({"user": user, "faculty_id": faculty_id}):
        favorites_col.insert_one({
            "user": user,
            "faculty_id": faculty_id,
            "timestamp": datetime.utcnow()
        })

def get_favorites(user):
    return list(favorites_col.find({"user": user}))

def get_faculty_by_id(fid):
    return faculty_col.find_one({"id": fid})

def clear_favorites(user):
    favorites_col.delete_many({"user": user})

def remove_from_favorites(user, faculty_id):
    favorites_col.delete_one({"user": user, "faculty_id": faculty_id})
