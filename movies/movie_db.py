# movies/movie_db.py
"""
💾 KINO DATABASE
MongoDB kino operatsiyalari
"""

from utils.db_config import movies

def create_movie(code, name, file_id, genre, formati):
    """Kino yaratish"""
    try: 
        movies.update_one(
            {"code":  code},
            {"$set":  {
                "file_id":  file_id,
                "name": name,
                "genre":  genre,
                "formati":  formati,
                "url": "@Saboq_kinolar",
                "urlbot": "@Saboq_kinolar_bot"
            }},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"❌ Kino yaratish xatosi: {e}")
        return False

def delete_movie_db(code):
    """Kino o'chirish"""
    try:
        result = movies.delete_one({"code": code})
        return result.deleted_count > 0
    except Exception as e:
        print(f"❌ Kino o'chirish xatosi: {e}")
        return False

def get_movie(code):
    """Kino olish"""
    try:
        return movies.find_one({"code": code})
    except Exception as e:
        print(f"❌ Kino olish xatosi: {e}")
        return None

def get_all_movies():
    """Barcha kinolar"""
    try:
        return list(movies.find({}, {"_id": 0}))
    except Exception as e: 
        print(f"❌ Kinolar olish xatosi: {e}")
        return []

def check_movie_code_exists(code):
    """Kino kodi bormi"""
    return movies.find_one({"code": code}) is not None