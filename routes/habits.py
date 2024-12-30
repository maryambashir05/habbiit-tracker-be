from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from database import supabase_client
import logging
from pydantic import BaseModel
from datetime import datetime
from auth import get_current_user

router = APIRouter(prefix="/habits", tags=["habits"])
logger = logging.getLogger(__name__)

class HabitCreate(BaseModel):
    name: str
    category: str
    color: str
    description: str | None = None

class HabitEntryCreate(BaseModel):
    date: str

@router.get("/")
async def get_habits(user_id: str = Depends(get_current_user), include_archived: bool = False) -> List[Dict]:
    try:
        response = supabase_client.from_('habits').select("*").eq('user_id', user_id)
        if not include_archived:
            response = response.eq('is_archived', False)
        result = response.execute()
        return result.data
    except Exception as e:
        logger.error(f"Failed to fetch habits: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/")
async def create_habit(habit: HabitCreate, user_id: str = Depends(get_current_user)) -> Dict:
    try:
        logger.info(f"Creating new habit: {habit.name} for user: {user_id}")
        
        # First verify that the user exists in the users table
        user = supabase_client.from_('users').select("*").eq('id', user_id).execute()
        if not user.data:
            logger.error(f"User {user_id} not found in users table")
            raise HTTPException(
                status_code=400,
                detail="User not found. Please try logging out and logging in again."
            )
        
        # Prepare habit data
        habit_data = {
            "name": habit.name,
            "category": habit.category,
            "color": habit.color,
            "description": habit.description,
            "is_archived": False,
            "streak_count": 0,
            "longest_streak": 0,
            "user_id": user_id
        }
        
        # Insert into Supabase
        response = supabase_client.from_('habits').insert(habit_data).execute()
        
        if not response.data:
            logger.error("Failed to create habit: No data returned")
            raise HTTPException(
                status_code=500,
                detail="Failed to create habit"
            )
        
        logger.info(f"Habit created successfully: {response.data[0]}")
        return response.data[0]
    except Exception as e:
        logger.error(f"Failed to create habit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/{habit_id}/entries")
async def create_habit_entry(
    habit_id: str, 
    entry: HabitEntryCreate, 
    user_id: str = Depends(get_current_user)
) -> Dict:
    try:
        logger.info(f"Creating entry for habit {habit_id} on {entry.date}")
        
        # Verify habit belongs to user
        habit = supabase_client.from_('habits').select("*").eq('id', habit_id).eq('user_id', user_id).execute()
        if not habit.data:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        # Get all entries for this habit, ordered by date
        entries = supabase_client.from_('habit_entries')\
            .select("*")\
            .eq('habit_id', habit_id)\
            .order('completed_at', desc=False)\
            .execute()
        
        # Calculate current streak
        current_streak = 0
        entry_date = datetime.strptime(entry.date, "%Y-%m-%d").date()
        
        if entries.data:
            # Convert all dates to date objects for comparison
            completion_dates = [datetime.strptime(e['completed_at'].split('T')[0], "%Y-%m-%d").date() for e in entries.data]
            completion_dates.append(entry_date)
            completion_dates.sort()
            
            # Calculate streak
            current_streak = 1
            for i in range(len(completion_dates)-1, 0, -1):
                date_diff = (completion_dates[i] - completion_dates[i-1]).days
                if date_diff == 1:  # Consecutive days
                    current_streak += 1
                else:
                    break
        else:
            current_streak = 1  # First entry starts streak at 1
        
        # Update habit with new streak information
        longest_streak = max(current_streak, habit.data[0]['longest_streak'])
        
        # Update the habit's streak information
        supabase_client.from_('habits')\
            .update({
                'streak_count': current_streak,
                'longest_streak': longest_streak
            })\
            .eq('id', habit_id)\
            .execute()
        
        # Prepare entry data
        entry_data = {
            "habit_id": habit_id,
            "completed_at": entry.date,
            "user_id": user_id
        }
        
        # Insert into Supabase
        response = supabase_client.from_('habit_entries').insert(entry_data).execute()
        
        if not response.data:
            logger.error("Failed to create habit entry: No data returned")
            raise HTTPException(
                status_code=500,
                detail="Failed to create habit entry"
            )
        
        logger.info(f"Habit entry created successfully: {response.data[0]}")
        return {
            **response.data[0],
            'streak_count': current_streak,
            'longest_streak': longest_streak
        }
    except Exception as e:
        logger.error(f"Failed to create habit entry: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/{habit_id}/entries")
async def get_habit_entries(
    habit_id: str,
    user_id: str = Depends(get_current_user),
    start_date: str | None = None,
    end_date: str | None = None
) -> List[Dict]:
    try:
        # Verify habit belongs to user
        habit = supabase_client.from_('habits').select("*").eq('id', habit_id).eq('user_id', user_id).execute()
        if not habit.data:
            raise HTTPException(status_code=404, detail="Habit not found")
            
        query = supabase_client.from_('habit_entries').select("*").eq('habit_id', habit_id).eq('user_id', user_id)
        
        if start_date:
            query = query.gte('completed_at', start_date)
        if end_date:
            query = query.lte('completed_at', end_date)
            
        result = query.execute()
        return result.data
    except Exception as e:
        logger.error(f"Failed to fetch habit entries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 

@router.delete("/{habit_id}")
async def delete_habit(habit_id: str, user_id: str = Depends(get_current_user)) -> Dict:
    try:
        logger.info(f"Attempting to delete habit {habit_id} for user {user_id}")
        
        # Verify habit belongs to user
        habit = supabase_client.from_('habits').select("*").eq('id', habit_id).eq('user_id', user_id).execute()
        if not habit.data:
            raise HTTPException(status_code=404, detail="Habit not found")
        
        # Delete habit entries first
        supabase_client.from_('habit_entries').delete().eq('habit_id', habit_id).execute()
        
        # Delete the habit
        response = supabase_client.from_('habits').delete().eq('id', habit_id).execute()
        
        if not response.data:
            logger.error("Failed to delete habit: No data returned")
            raise HTTPException(
                status_code=500,
                detail="Failed to delete habit"
            )
        
        logger.info(f"Habit {habit_id} deleted successfully")
        return {"message": "Habit deleted successfully"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Failed to delete habit: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 