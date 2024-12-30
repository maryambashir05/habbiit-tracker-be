from fastapi import APIRouter, HTTPException, Depends, Response, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict
from database import supabase_client
import logging
import traceback
from datetime import datetime
from auth import create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

@router.post("/signin")
async def signin(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict:
    try:
        logger.info(f"Attempting login for user: {form_data.username}")
        
        # Sign in with Supabase
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        if not auth_response.user or not auth_response.session:
            logger.error("Authentication failed: No session or user returned")
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        
        # Create our own JWT token
        token = create_access_token(
            user_id=auth_response.user.id,
            email=auth_response.user.email
        )
        
        logger.info("Login successful")
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if "Invalid login credentials" in str(e):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/signup")
async def signup(signup_data: SignupRequest) -> Dict:
    try:
        email = signup_data.email.lower().strip()
        username = signup_data.username.strip()
        logger.info(f"Attempting to create user: {email}")
        
        # Check if username is taken
        existing_user = supabase_client.from_('users').select("*").eq('username', username).execute()
        if existing_user.data:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Sign up with Supabase
        auth_response = supabase_client.auth.sign_up({
            "email": email,
            "password": signup_data.password,
            "options": {
                "data": {
                    "username": username
                },
                "email_confirm": True
            }
        })
        
        if not auth_response.user:
            logger.error("User creation failed: No user returned")
            raise HTTPException(
                status_code=400,
                detail="Failed to create user"
            )

        # Create user record in public.users table
        try:
            user_data = {
                "id": auth_response.user.id,
                "username": username,
                "email": email,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            supabase_client.from_('users').insert(user_data).execute()
            logger.info(f"User record created in public.users: {auth_response.user.id}")
        except Exception as e:
            logger.error(f"Failed to create user record in public.users: {str(e)}")
            # Clean up auth user if user record creation fails
            try:
                supabase_client.auth.admin.delete_user(auth_response.user.id)
            except:
                pass
            raise HTTPException(
                status_code=500,
                detail="Failed to create user record"
            )
        
        # Create JWT token immediately after signup
        token = create_access_token(
            user_id=auth_response.user.id,
            email=auth_response.user.email
        )
        return {
            "access_token": token,
            "token_type": "bearer"
        }
            
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if "already registered" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.post("/logout")
async def logout(response: Response) -> Dict:
    try:
        logger.info("Attempting to logout user")
        response.delete_cookie(key="token")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to logout: {str(e)}"
        )

@router.get("/test-connection")
async def test_connection():
    try:
        # Test database connection
        response = supabase_client.from_('users').select("*").execute()
        return {
            "status": "success",
            "message": "Database connection successful",
            "user_count": len(response.data)
        }
    except Exception as e:
        logger.error(f"Test connection failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 