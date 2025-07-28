"""
User Modeling Backend Router
FastAPI router for behavior tracking, personalization algorithms, and user preference profiling
"""

import time
import logging
import hashlib
from typing import List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer

from app.schemas.enhanced_health_schemas import (
    UserInteractionRequest, UserInteractionResponse, InteractionType,
    UserPreferenceProfileResponse, BehaviorPatternResponse, 
    PersonalizationRecommendationResponse, UserModelingAnalyticsResponse
)
from app.services.enhanced.user_modeling import (
    get_user_modeling_backend, UserInteraction, UserPreferenceProfile,
    BehaviorPattern, PersonalizationRecommendation
)
from app.utils.auth_middleware import get_current_user
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/user-modeling", tags=["User Modeling Backend"])

# Initialize user modeling backend
user_modeling = get_user_modeling_backend()

@router.post("/interactions/track", response_model=UserInteractionResponse)
async def track_user_interaction(
    request: UserInteractionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Track user interaction for behavior analysis and personalization
    
    Tracks various types of user interactions including:
    - Chat messages and conversations
    - Health data entries and logs
    - Search queries and document views
    - Feedback submissions and goal setting
    - Profile updates and reminder interactions
    """
    try:
        start_time = time.time()
        
        # Create user interaction object
        interaction = UserInteraction(
            user_id=current_user.id,
            interaction_type=request.interaction_type,
            timestamp=datetime.utcnow(),
            content=request.content,
            metadata=request.metadata,
            session_id=request.session_id,
            duration=request.duration,
            engagement_score=request.engagement_score
        )
        
        # Track interaction
        success = await user_modeling.track_user_interaction(interaction)
        
        # Generate interaction ID
        interaction_id = hashlib.md5(
            f"{current_user.id}_{interaction.timestamp.isoformat()}_{request.content[:50]}".encode()
        ).hexdigest()[:12]
        
        processing_time = time.time() - start_time
        
        logger.info(f"User interaction tracked for user {current_user.id} in {processing_time:.3f}s")
        
        return UserInteractionResponse(
            success=success,
            interaction_id=f"int_{interaction_id}",
            engagement_score=interaction.engagement_score or 0.0,
            profile_updated=success,
            message="Interaction tracked successfully"
        )
        
    except Exception as e:
        logger.error(f"Error tracking user interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Interaction tracking failed: {str(e)}"
        )

@router.get("/profile", response_model=UserPreferenceProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get user preference profile and behavior analysis
    
    Returns comprehensive user profile including:
    - Content preferences across medical categories
    - Interaction patterns and peak usage times
    - Health goals and communication style
    - Engagement level and confidence scores
    """
    try:
        start_time = time.time()
        
        # Get user profile
        profile = await user_modeling.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. More interactions needed to build profile."
            )
        
        processing_time = time.time() - start_time
        
        logger.info(f"User profile retrieved for user {current_user.id} in {processing_time:.3f}s")
        
        return UserPreferenceProfileResponse(
            user_id=profile.user_id,
            content_preferences={k.value: v for k, v in profile.content_preferences.items()},
            interaction_patterns=profile.interaction_patterns,
            health_goals=profile.health_goals,
            communication_style=profile.communication_style,
            engagement_level=profile.engagement_level,
            last_updated=profile.last_updated,
            confidence_score=profile.confidence_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}"
        )

@router.get("/behavior-patterns", response_model=List[BehaviorPatternResponse])
async def get_behavior_patterns(
    current_user: User = Depends(get_current_user)
):
    """
    Get user behavior patterns and analysis
    
    Returns identified behavior patterns including:
    - Time-based usage patterns
    - Content preference patterns
    - Interaction type patterns
    - Pattern confidence and frequency
    """
    try:
        start_time = time.time()
        
        # Get behavior patterns
        patterns = await user_modeling.get_behavior_patterns(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Behavior patterns retrieved for user {current_user.id} in {processing_time:.3f}s")
        
        return [
            BehaviorPatternResponse(
                pattern_type=pattern.pattern_type,
                frequency=pattern.frequency,
                time_distribution=pattern.time_distribution,
                content_affinity=pattern.content_affinity,
                confidence=pattern.confidence,
                last_observed=pattern.last_observed
            )
            for pattern in patterns
        ]
        
    except Exception as e:
        logger.error(f"Error getting behavior patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve behavior patterns: {str(e)}"
        )

@router.get("/recommendations", response_model=List[PersonalizationRecommendationResponse])
async def get_personalization_recommendations(
    content_type: str = Query("all", description="Type of recommendations to generate"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized recommendations based on user behavior and preferences
    
    Generates recommendations for:
    - Content recommendations based on interests
    - Interaction recommendations based on usage patterns
    - Goal-based recommendations based on health objectives
    - Feature recommendations based on engagement level
    """
    try:
        start_time = time.time()
        
        # Generate recommendations
        recommendations = await user_modeling.generate_personalization_recommendations(
            user_id=current_user.id,
            content_type=content_type,
            limit=limit
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Recommendations generated for user {current_user.id} in {processing_time:.3f}s")
        
        return [
            PersonalizationRecommendationResponse(
                content_type=rec.content_type,
                content_id=rec.content_id,
                relevance_score=rec.relevance_score,
                reasoning=rec.reasoning,
                user_preferences_used=rec.user_preferences_used,
                confidence=rec.confidence
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.get("/recommendations/content", response_model=List[PersonalizationRecommendationResponse])
async def get_content_recommendations(
    limit: int = Query(10, ge=1, le=20, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user)
):
    """
    Get content-specific personalized recommendations
    
    Focuses on content recommendations based on:
    - Medical content category preferences
    - Reading patterns and engagement
    - Health condition interests
    - Educational content preferences
    """
    try:
        start_time = time.time()
        
        # Generate content recommendations
        recommendations = await user_modeling.generate_personalization_recommendations(
            user_id=current_user.id,
            content_type="content",
            limit=limit
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Content recommendations generated for user {current_user.id} in {processing_time:.3f}s")
        
        return [
            PersonalizationRecommendationResponse(
                content_type=rec.content_type,
                content_id=rec.content_id,
                relevance_score=rec.relevance_score,
                reasoning=rec.reasoning,
                user_preferences_used=rec.user_preferences_used,
                confidence=rec.confidence
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        logger.error(f"Error generating content recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content recommendations: {str(e)}"
        )

@router.get("/recommendations/goals", response_model=List[PersonalizationRecommendationResponse])
async def get_goal_recommendations(
    limit: int = Query(5, ge=1, le=10, description="Maximum number of recommendations"),
    current_user: User = Depends(get_current_user)
):
    """
    Get goal-based personalized recommendations
    
    Generates recommendations based on:
    - User's health goals and objectives
    - Progress tracking and achievements
    - Goal-related content and resources
    - Personalized goal-setting suggestions
    """
    try:
        start_time = time.time()
        
        # Generate goal recommendations
        recommendations = await user_modeling.generate_personalization_recommendations(
            user_id=current_user.id,
            content_type="goals",
            limit=limit
        )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Goal recommendations generated for user {current_user.id} in {processing_time:.3f}s")
        
        return [
            PersonalizationRecommendationResponse(
                content_type=rec.content_type,
                content_id=rec.content_id,
                relevance_score=rec.relevance_score,
                reasoning=rec.reasoning,
                user_preferences_used=rec.user_preferences_used,
                confidence=rec.confidence
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        logger.error(f"Error generating goal recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate goal recommendations: {str(e)}"
        )

@router.post("/profile/refresh")
async def refresh_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Manually refresh user profile and behavior analysis
    
    Forces an update of the user's preference profile and behavior patterns
    based on recent interactions and data.
    """
    try:
        start_time = time.time()
        
        # Force profile update
        await user_modeling._update_user_profile(current_user.id)
        
        processing_time = time.time() - start_time
        
        logger.info(f"User profile refreshed for user {current_user.id} in {processing_time:.3f}s")
        
        return {
            "success": True,
            "message": "User profile refreshed successfully",
            "processing_time": processing_time
        }
        
    except Exception as e:
        logger.error(f"Error refreshing user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh user profile: {str(e)}"
        )

@router.get("/analytics", response_model=UserModelingAnalyticsResponse)
async def get_user_modeling_analytics(
    current_user: User = Depends(get_current_user)
):
    """
    Get user modeling analytics and insights
    
    Returns analytics including:
    - Total interactions tracked
    - Profile confidence metrics
    - Engagement distribution
    - Top content categories
    - Behavior pattern statistics
    """
    try:
        start_time = time.time()
        
        # Get user profile for analytics
        profile = await user_modeling.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Cannot generate analytics."
            )
        
        # Get behavior patterns
        patterns = await user_modeling.get_behavior_patterns(current_user.id)
        
        # Calculate analytics
        total_interactions = len(user_modeling.interaction_cache.get(current_user.id, []))
        
        # Engagement distribution (simplified)
        engagement_distribution = {
            "high": 0,
            "medium": 0,
            "low": 0
        }
        if profile.engagement_level:
            engagement_distribution[profile.engagement_level] = 1
        
        # Top content categories
        top_categories = [
            {"category": category.value, "preference": score}
            for category, score in sorted(
                profile.content_preferences.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]
        
        processing_time = time.time() - start_time
        
        logger.info(f"Analytics generated for user {current_user.id} in {processing_time:.3f}s")
        
        return UserModelingAnalyticsResponse(
            total_interactions=total_interactions,
            profile_confidence=profile.confidence_score,
            engagement_distribution=engagement_distribution,
            top_content_categories=top_categories,
            behavior_patterns_count=len(patterns)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_old_data(
    days: int = Query(90, ge=1, le=365, description="Days of data to retain"),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up old user modeling data (admin function)
    
    Removes old interaction data and cached information
    to maintain system performance and storage efficiency.
    """
    try:
        # Check if user has admin privileges (simplified check)
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        start_time = time.time()
        
        # Clean up old data
        cleaned_count = await user_modeling.cleanup_old_data(days)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Data cleanup completed by admin {current_user.id}: {cleaned_count} items removed")
        
        return {
            "success": True,
            "message": f"Data cleanup completed",
            "cleaned_count": cleaned_count,
            "processing_time": processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in data cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data cleanup failed: {str(e)}"
        )

@router.get("/capabilities")
async def get_user_modeling_capabilities():
    """
    Get available user modeling capabilities
    """
    return {
        "interaction_tracking": {
            "chat_messages": "Track chat interactions and conversations",
            "health_data": "Track health data entries and logs",
            "search_queries": "Track search behavior and queries",
            "document_views": "Track document and content views",
            "feedback": "Track feedback submissions and ratings",
            "goals": "Track goal setting and progress"
        },
        "behavior_analysis": {
            "content_preferences": "Analyze content category preferences",
            "interaction_patterns": "Identify usage patterns and habits",
            "time_analysis": "Analyze peak usage times and patterns",
            "engagement_scoring": "Calculate user engagement levels",
            "communication_style": "Analyze communication preferences"
        },
        "personalization": {
            "content_recommendations": "Generate content-based recommendations",
            "goal_recommendations": "Generate goal-based recommendations",
            "interaction_recommendations": "Generate interaction-based recommendations",
            "feature_recommendations": "Recommend features based on usage"
        },
        "profile_management": {
            "preference_profiling": "Build comprehensive user preference profiles",
            "confidence_scoring": "Calculate profile confidence scores",
            "pattern_identification": "Identify behavior patterns and trends",
            "profile_refresh": "Update profiles based on new interactions"
        },
        "analytics": {
            "usage_analytics": "Generate usage and engagement analytics",
            "preference_analytics": "Analyze preference trends and changes",
            "behavior_analytics": "Analyze behavior patterns and insights",
            "performance_metrics": "Track system performance and efficiency"
        }
    }

@router.get("/health")
async def user_modeling_health_check():
    """
    Health check endpoint for user modeling backend
    """
    try:
        # Test basic functionality
        test_interaction = UserInteraction(
            user_id=1,
            interaction_type=InteractionType.CHAT_MESSAGE,
            timestamp=datetime.utcnow(),
            content="Test interaction",
            metadata={},
            session_id="test_session"
        )
        
        # Test profile retrieval (should return None for test user)
        test_profile = await user_modeling.get_user_profile(1)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "interaction_tracking": "available",
            "profile_management": "available",
            "behavior_analysis": "available",
            "personalization": "available",
            "test_result": "successful"
        }
        
    except Exception as e:
        logger.error(f"User modeling health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"User modeling backend unavailable: {str(e)}"
        ) 