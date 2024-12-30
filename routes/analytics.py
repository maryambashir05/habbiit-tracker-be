from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
from database import supabase_client
import logging
from auth import get_current_user
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

class HabitPerformance(BaseModel):
    id: str
    name: str
    category: str
    completion_rate: float
    streak_count: int
    longest_streak: int

@router.get("/summary")
async def get_analytics_summary(user_id: str = Depends(get_current_user)) -> Dict:
    try:
        habits = supabase_client.from_('habits').select("*").eq('user_id', user_id).execute()
        entries = supabase_client.from_('habit_entries').select("*").eq('user_id', user_id).execute()
        
        # Calculate current streak (max streak among all habits)
        current_streak = max([h.get('streak_count', 0) for h in habits.data]) if habits.data else 0

        # Calculate longest streak (max longest_streak among all habits)
        longest_streak = max([h.get('longest_streak', 0) for h in habits.data]) if habits.data else 0
        
        return {
            "total_habits": len(habits.data),
            "total_entries": len(entries.data),
            "active_habits": len([h for h in habits.data if not h.get('is_archived', False)]),
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }
    except Exception as e:
        logger.error(f"Failed to fetch analytics summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/performance", response_model=List[HabitPerformance])
async def get_habit_performance(user_id: str = Depends(get_current_user)) -> List[Dict]:
    try:
        # Get all habits
        habits = supabase_client.from_('habits').select("*").eq('user_id', user_id).execute()
        
        # Get entries for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        entries = supabase_client.from_('habit_entries')\
            .select("*")\
            .eq('user_id', user_id)\
            .gte('completed_at', start_date.strftime('%Y-%m-%d'))\
            .lte('completed_at', end_date.strftime('%Y-%m-%d'))\
            .execute()

        # Calculate performance for each habit
        performance_data = []
        for habit in habits.data:
            # Count entries for this habit
            habit_entries = [e for e in entries.data if e['habit_id'] == habit['id']]
            completion_rate = (len(habit_entries) / 30) * 100  # 30 days period

            performance_data.append({
                "id": habit['id'],
                "name": habit['name'],
                "category": habit['category'],
                "completion_rate": round(completion_rate, 1),
                "streak_count": habit.get('streak_count', 0),
                "longest_streak": habit.get('longest_streak', 0)
            })

        # Sort by completion rate descending
        performance_data.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        return performance_data
    except Exception as e:
        logger.error(f"Failed to fetch habit performance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 