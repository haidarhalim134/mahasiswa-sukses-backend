
from fastapi import APIRouter

from app.modules.community.schemas import CommunityStats, ForumPostCreate, ForumPostRead, ForumTab


router = APIRouter(prefix="/api/v1/community", tags=["community"])

@router.get("/forum/stats", response_model=CommunityStats, tags=["Forum"])
async def get_community_stats():
    """Returns the '1,234 mahasiswa online' count."""
    raise NotImplementedError

@router.get("/forum/feed", response_model=list[ForumPostRead], tags=["Forum"])
async def get_forum_feed(tab: ForumTab = ForumTab.POSTINGAN):
    """
    Returns the feed for either 'Postingan' or 'Ruang Belajar'.
    Includes tags like #Algoritma or #Tips.
    """
    raise NotImplementedError

# 2. Interactions (Postingan)
@router.post("/forum/posts", response_model=ForumPostRead, status_code=201, tags=["Forum"])
async def create_post(post: ForumPostCreate):
    """Triggered by the '+' floating action button."""
    raise NotImplementedError

@router.post("/forum/posts/{post_id}/like", tags=["Forum"])
async def like_post(post_id: int):
    """Toggles the heart icon interaction."""
    raise NotImplementedError

# 3. Ruang Belajar (Study Rooms)
@router.post("/forum/rooms/{room_id}/join", tags=["Forum"])
async def join_study_room(room_id: int):
    """Handles the 'Join' button for study sessions."""
    raise NotImplementedError

@router.get("/forum/posts/{post_id}/comments", tags=["Forum"])
async def get_post_comments(post_id: int):
    """Fetches the discussion thread for a specific post."""
    raise NotImplementedError