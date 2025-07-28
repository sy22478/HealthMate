"""
User Modeling Backend Service
Behavior tracking infrastructure, personalization algorithms, and user preference profiling system
"""

import asyncio
import logging
import json
import hashlib
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, Counter
import pickle
import base64

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.user import User
from app.models.enhanced_health_models import UserPreference, ConversationHistory
from app.database import get_db
from app.exceptions.external_api_exceptions import ExternalAPIError
from app.utils.encryption_utils import field_encryption

logger = logging.getLogger(__name__)

class InteractionType(str, Enum):
    """User interaction types"""
    CHAT_MESSAGE = "chat_message"
    HEALTH_DATA_ENTRY = "health_data_entry"
    MEDICATION_LOG = "medication_log"
    SYMPTOM_LOG = "symptom_log"
    SEARCH_QUERY = "search_query"
    DOCUMENT_VIEW = "document_view"
    FEEDBACK_SUBMISSION = "feedback_submission"
    GOAL_SETTING = "goal_setting"
    REMINDER_INTERACTION = "reminder_interaction"
    PROFILE_UPDATE = "profile_update"

class ContentCategory(str, Enum):
    """Content categories for personalization"""
    DIABETES = "diabetes"
    CARDIOVASCULAR = "cardiovascular"
    MENTAL_HEALTH = "mental_health"
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    MEDICATION = "medication"
    SYMPTOMS = "symptoms"
    PREVENTIVE_CARE = "preventive_care"
    EMERGENCY = "emergency"
    GENERAL_HEALTH = "general_health"

class PreferenceStrength(str, Enum):
    """Preference strength levels"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEUTRAL = "neutral"

@dataclass
class UserInteraction:
    """User interaction data structure"""
    user_id: int
    interaction_type: InteractionType
    timestamp: datetime
    content: str
    metadata: Dict[str, Any]
    session_id: str
    duration: Optional[float] = None
    engagement_score: Optional[float] = None

@dataclass
class UserPreferenceProfile:
    """User preference profile"""
    user_id: int
    content_preferences: Dict[ContentCategory, float]
    interaction_patterns: Dict[str, Any]
    health_goals: List[str]
    communication_style: str
    engagement_level: str
    last_updated: datetime
    confidence_score: float

@dataclass
class BehaviorPattern:
    """User behavior pattern"""
    pattern_type: str
    frequency: float
    time_distribution: Dict[str, float]
    content_affinity: Dict[str, float]
    confidence: float
    last_observed: datetime

@dataclass
class PersonalizationRecommendation:
    """Personalization recommendation"""
    content_type: str
    content_id: str
    relevance_score: float
    reasoning: str
    user_preferences_used: List[str]
    confidence: float

class UserModelingBackend:
    """Advanced user modeling backend for personalization"""
    
    def __init__(self, 
                 interaction_retention_days: int = 90,
                 preference_update_frequency_hours: int = 24,
                 min_interactions_for_profile: int = 10):
        self.interaction_retention_days = interaction_retention_days
        self.preference_update_frequency_hours = preference_update_frequency_hours
        self.min_interactions_for_profile = min_interactions_for_profile
        
        # In-memory caches for performance
        self.user_profiles: Dict[int, UserPreferenceProfile] = {}
        self.behavior_patterns: Dict[int, List[BehaviorPattern]] = {}
        self.interaction_cache: Dict[int, List[UserInteraction]] = {}
        
        # Content category keywords for classification
        self.content_keywords = self._initialize_content_keywords()
        
        # Engagement scoring weights
        self.engagement_weights = {
            'duration': 0.3,
            'interaction_depth': 0.4,
            'frequency': 0.2,
            'feedback': 0.1
        }
        
        logger.info("User Modeling Backend initialized successfully")
    
    def _initialize_content_keywords(self) -> Dict[ContentCategory, List[str]]:
        """Initialize content category keywords"""
        return {
            ContentCategory.DIABETES: [
                'diabetes', 'blood sugar', 'insulin', 'glucose', 'A1C', 'diabetic',
                'hyperglycemia', 'hypoglycemia', 'diabetic neuropathy'
            ],
            ContentCategory.CARDIOVASCULAR: [
                'heart', 'cardiac', 'cardiovascular', 'blood pressure', 'hypertension',
                'cholesterol', 'heart attack', 'stroke', 'arrhythmia'
            ],
            ContentCategory.MENTAL_HEALTH: [
                'depression', 'anxiety', 'stress', 'mental health', 'therapy',
                'psychology', 'mood', 'emotional', 'cognitive'
            ],
            ContentCategory.NUTRITION: [
                'nutrition', 'diet', 'food', 'calories', 'vitamins', 'minerals',
                'protein', 'carbohydrates', 'fats', 'meal planning'
            ],
            ContentCategory.EXERCISE: [
                'exercise', 'workout', 'fitness', 'physical activity', 'training',
                'cardio', 'strength training', 'yoga', 'walking'
            ],
            ContentCategory.MEDICATION: [
                'medication', 'drug', 'prescription', 'dosage', 'side effects',
                'pharmacy', 'pill', 'injection', 'treatment'
            ],
            ContentCategory.SYMPTOMS: [
                'symptom', 'pain', 'fever', 'headache', 'nausea', 'fatigue',
                'dizziness', 'shortness of breath', 'chest pain'
            ],
            ContentCategory.PREVENTIVE_CARE: [
                'prevention', 'screening', 'vaccination', 'checkup', 'wellness',
                'preventive', 'early detection', 'health maintenance'
            ],
            ContentCategory.EMERGENCY: [
                'emergency', 'urgent', 'critical', 'severe', 'acute', '911',
                'emergency room', 'ambulance', 'life-threatening'
            ],
            ContentCategory.GENERAL_HEALTH: [
                'health', 'wellness', 'lifestyle', 'general', 'overall health',
                'health tips', 'healthy living'
            ]
        }
    
    async def track_user_interaction(self, interaction: UserInteraction) -> bool:
        """Track user interaction for behavior analysis"""
        try:
            # Store interaction in cache
            if interaction.user_id not in self.interaction_cache:
                self.interaction_cache[interaction.user_id] = []
            
            self.interaction_cache[interaction.user_id].append(interaction)
            
            # Calculate engagement score if not provided
            if interaction.engagement_score is None:
                interaction.engagement_score = self._calculate_engagement_score(interaction)
            
            # Store in database
            await self._store_interaction_db(interaction)
            
            # Update user profile if enough interactions
            await self._update_user_profile_if_needed(interaction.user_id)
            
            logger.info(f"Tracked interaction for user {interaction.user_id}: {interaction.interaction_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking user interaction: {e}")
            raise ExternalAPIError(f"Failed to track interaction: {str(e)}")
    
    def _calculate_engagement_score(self, interaction: UserInteraction) -> float:
        """Calculate engagement score for interaction"""
        score = 0.0
        
        # Duration-based scoring
        if interaction.duration:
            if interaction.duration > 300:  # 5+ minutes
                score += 0.4
            elif interaction.duration > 60:  # 1+ minutes
                score += 0.3
            elif interaction.duration > 10:  # 10+ seconds
                score += 0.2
        
        # Interaction type scoring
        type_scores = {
            InteractionType.CHAT_MESSAGE: 0.3,
            InteractionType.HEALTH_DATA_ENTRY: 0.4,
            InteractionType.MEDICATION_LOG: 0.5,
            InteractionType.SYMPTOM_LOG: 0.5,
            InteractionType.SEARCH_QUERY: 0.2,
            InteractionType.DOCUMENT_VIEW: 0.3,
            InteractionType.FEEDBACK_SUBMISSION: 0.6,
            InteractionType.GOAL_SETTING: 0.7,
            InteractionType.REMINDER_INTERACTION: 0.4,
            InteractionType.PROFILE_UPDATE: 0.3
        }
        
        score += type_scores.get(interaction.interaction_type, 0.2)
        
        # Content length scoring
        content_length = len(interaction.content)
        if content_length > 500:
            score += 0.2
        elif content_length > 100:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _store_interaction_db(self, interaction: UserInteraction):
        """Store interaction in database"""
        try:
            db = next(get_db())
            
            # Store in conversation history if it's a chat message
            if interaction.interaction_type == InteractionType.CHAT_MESSAGE:
                conversation_entry = ConversationHistory(
                    user_id=interaction.user_id,
                    message_content=interaction.content,
                    timestamp=interaction.timestamp,
                    message_type="user",
                    session_id=interaction.session_id,
                    metadata=json.dumps(interaction.metadata)
                )
                db.add(conversation_entry)
            
            # Store in user preferences for analysis
            preference_entry = UserPreference(
                user_id=interaction.user_id,
                preference_type=interaction.interaction_type.value,
                preference_value=interaction.content[:500],  # Truncate if too long
                strength=PreferenceStrength.MODERATE.value,
                last_updated=interaction.timestamp,
                metadata=json.dumps(interaction.metadata)
            )
            db.add(preference_entry)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error storing interaction in database: {e}")
            raise ExternalAPIError(f"Database storage failed: {str(e)}")
    
    async def _update_user_profile_if_needed(self, user_id: int):
        """Update user profile if enough new interactions"""
        try:
            # Check if profile update is needed
            if user_id in self.user_profiles:
                last_update = self.user_profiles[user_id].last_updated
                hours_since_update = (datetime.utcnow() - last_update).total_seconds() / 3600
                
                if hours_since_update < self.preference_update_frequency_hours:
                    return  # Too soon to update
            
            # Count recent interactions
            recent_interactions = await self._get_recent_interactions(user_id, days=7)
            
            if len(recent_interactions) >= self.min_interactions_for_profile:
                await self._update_user_profile(user_id)
                
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
    
    async def _get_recent_interactions(self, user_id: int, days: int = 7) -> List[UserInteraction]:
        """Get recent interactions for user"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get from cache first
            if user_id in self.interaction_cache:
                cached_interactions = [
                    interaction for interaction in self.interaction_cache[user_id]
                    if interaction.timestamp >= cutoff_date
                ]
                if len(cached_interactions) > 0:
                    return cached_interactions
            
            # Get from database
            db = next(get_db())
            
            # Get conversation history
            conversations = db.query(ConversationHistory).filter(
                and_(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.timestamp >= cutoff_date
                )
            ).all()
            
            # Get user preferences
            preferences = db.query(UserPreference).filter(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.last_updated >= cutoff_date
                )
            ).all()
            
            # Convert to UserInteraction objects
            interactions = []
            
            for conv in conversations:
                interaction = UserInteraction(
                    user_id=conv.user_id,
                    interaction_type=InteractionType.CHAT_MESSAGE,
                    timestamp=conv.timestamp,
                    content=conv.message_content,
                    metadata=json.loads(conv.metadata) if conv.metadata else {},
                    session_id=conv.session_id
                )
                interactions.append(interaction)
            
            for pref in preferences:
                interaction = UserInteraction(
                    user_id=pref.user_id,
                    interaction_type=InteractionType(pref.preference_type),
                    timestamp=pref.last_updated,
                    content=pref.preference_value,
                    metadata=json.loads(pref.metadata) if pref.metadata else {},
                    session_id=""
                )
                interactions.append(interaction)
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error getting recent interactions: {e}")
            return []
    
    async def _update_user_profile(self, user_id: int):
        """Update user preference profile"""
        try:
            # Get recent interactions
            interactions = await self._get_recent_interactions(user_id, days=30)
            
            if len(interactions) < 5:
                return  # Not enough data
            
            # Analyze content preferences
            content_preferences = self._analyze_content_preferences(interactions)
            
            # Analyze interaction patterns
            interaction_patterns = self._analyze_interaction_patterns(interactions)
            
            # Analyze health goals
            health_goals = self._extract_health_goals(interactions)
            
            # Determine communication style
            communication_style = self._analyze_communication_style(interactions)
            
            # Calculate engagement level
            engagement_level = self._calculate_engagement_level(interactions)
            
            # Calculate confidence score
            confidence_score = self._calculate_profile_confidence(interactions)
            
            # Create or update profile
            profile = UserPreferenceProfile(
                user_id=user_id,
                content_preferences=content_preferences,
                interaction_patterns=interaction_patterns,
                health_goals=health_goals,
                communication_style=communication_style,
                engagement_level=engagement_level,
                last_updated=datetime.utcnow(),
                confidence_score=confidence_score
            )
            
            self.user_profiles[user_id] = profile
            
            # Update behavior patterns
            self.behavior_patterns[user_id] = self._identify_behavior_patterns(interactions)
            
            logger.info(f"Updated user profile for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise ExternalAPIError(f"Profile update failed: {str(e)}")
    
    def _analyze_content_preferences(self, interactions: List[UserInteraction]) -> Dict[ContentCategory, float]:
        """Analyze user content preferences"""
        preferences = {category: 0.0 for category in ContentCategory}
        total_interactions = len(interactions)
        
        if total_interactions == 0:
            return preferences
        
        for interaction in interactions:
            content_lower = interaction.content.lower()
            
            for category, keywords in self.content_keywords.items():
                keyword_matches = sum(1 for keyword in keywords if keyword in content_lower)
                if keyword_matches > 0:
                    # Weight by engagement score and frequency
                    weight = (keyword_matches / len(keywords)) * (interaction.engagement_score or 0.5)
                    preferences[category] += weight
        
        # Normalize preferences
        max_preference = max(preferences.values()) if preferences.values() else 1.0
        if max_preference > 0:
            for category in preferences:
                preferences[category] = preferences[category] / max_preference
        
        return preferences
    
    def _analyze_interaction_patterns(self, interactions: List[UserInteraction]) -> Dict[str, Any]:
        """Analyze user interaction patterns"""
        patterns = {
            'peak_hours': {},
            'interaction_types': {},
            'session_duration': 0.0,
            'frequency': 0.0,
            'response_time': 0.0
        }
        
        if not interactions:
            return patterns
        
        # Analyze peak hours
        hour_counts = Counter()
        for interaction in interactions:
            hour = interaction.timestamp.hour
            hour_counts[hour] += 1
        
        patterns['peak_hours'] = dict(hour_counts.most_common(3))
        
        # Analyze interaction types
        type_counts = Counter()
        for interaction in interactions:
            type_counts[interaction.interaction_type.value] += 1
        
        patterns['interaction_types'] = dict(type_counts)
        
        # Calculate average session duration
        durations = [interaction.duration for interaction in interactions if interaction.duration]
        if durations:
            patterns['session_duration'] = sum(durations) / len(durations)
        
        # Calculate interaction frequency (interactions per day)
        if interactions:
            date_range = (interactions[-1].timestamp - interactions[0].timestamp).days + 1
            patterns['frequency'] = len(interactions) / max(date_range, 1)
        
        return patterns
    
    def _extract_health_goals(self, interactions: List[UserInteraction]) -> List[str]:
        """Extract health goals from interactions"""
        goals = []
        goal_keywords = [
            'goal', 'target', 'aim', 'objective', 'want to', 'trying to',
            'working on', 'focus on', 'improve', 'reduce', 'increase'
        ]
        
        for interaction in interactions:
            content_lower = interaction.content.lower()
            
            for keyword in goal_keywords:
                if keyword in content_lower:
                    # Extract goal-related content
                    sentences = interaction.content.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            goals.append(sentence.strip())
                            break
        
        # Remove duplicates and limit to top 5
        unique_goals = list(set(goals))
        return unique_goals[:5]
    
    def _analyze_communication_style(self, interactions: List[UserInteraction]) -> str:
        """Analyze user communication style"""
        if not interactions:
            return "formal"
        
        # Analyze text characteristics
        avg_length = sum(len(interaction.content) for interaction in interactions) / len(interactions)
        formal_indicators = 0
        casual_indicators = 0
        
        for interaction in interactions:
            content = interaction.content.lower()
            
            # Formal indicators
            if any(word in content for word in ['please', 'thank you', 'would you', 'could you']):
                formal_indicators += 1
            
            # Casual indicators
            if any(word in content for word in ['hey', 'hi', 'thanks', 'cool', 'awesome']):
                casual_indicators += 1
        
        if formal_indicators > casual_indicators:
            return "formal"
        elif casual_indicators > formal_indicators:
            return "casual"
        else:
            return "neutral"
    
    def _calculate_engagement_level(self, interactions: List[UserInteraction]) -> str:
        """Calculate user engagement level"""
        if not interactions:
            return "low"
        
        avg_engagement = sum(interaction.engagement_score or 0 for interaction in interactions) / len(interactions)
        
        if avg_engagement > 0.7:
            return "high"
        elif avg_engagement > 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_profile_confidence(self, interactions: List[UserInteraction]) -> float:
        """Calculate confidence score for user profile"""
        if not interactions:
            return 0.0
        
        # Factors affecting confidence
        interaction_count = len(interactions)
        time_span = (interactions[-1].timestamp - interactions[0].timestamp).days
        avg_engagement = sum(interaction.engagement_score or 0 for interaction in interactions) / len(interactions)
        
        # Calculate confidence based on factors
        count_score = min(interaction_count / 50.0, 1.0)  # Max at 50 interactions
        time_score = min(time_span / 30.0, 1.0)  # Max at 30 days
        engagement_score = avg_engagement
        
        # Weighted average
        confidence = (count_score * 0.4 + time_score * 0.3 + engagement_score * 0.3)
        
        return min(confidence, 1.0)
    
    def _identify_behavior_patterns(self, interactions: List[UserInteraction]) -> List[BehaviorPattern]:
        """Identify behavior patterns from interactions"""
        patterns = []
        
        if not interactions:
            return patterns
        
        # Time-based patterns
        time_pattern = self._analyze_time_patterns(interactions)
        if time_pattern:
            patterns.append(time_pattern)
        
        # Content-based patterns
        content_pattern = self._analyze_content_patterns(interactions)
        if content_pattern:
            patterns.append(content_pattern)
        
        # Interaction-based patterns
        interaction_pattern = self._analyze_interaction_patterns_detailed(interactions)
        if interaction_pattern:
            patterns.append(interaction_pattern)
        
        return patterns
    
    def _analyze_time_patterns(self, interactions: List[UserInteraction]) -> Optional[BehaviorPattern]:
        """Analyze time-based behavior patterns"""
        if len(interactions) < 5:
            return None
        
        # Group by hour
        hour_counts = Counter()
        for interaction in interactions:
            hour = interaction.timestamp.hour
            hour_counts[hour] += 1
        
        # Find peak hours
        total_interactions = len(interactions)
        peak_hours = {}
        for hour, count in hour_counts.items():
            frequency = count / total_interactions
            if frequency > 0.1:  # More than 10% of interactions
                peak_hours[str(hour)] = frequency
        
        if peak_hours:
            return BehaviorPattern(
                pattern_type="time_distribution",
                frequency=1.0,
                time_distribution=peak_hours,
                content_affinity={},
                confidence=min(len(peak_hours) / 24.0, 1.0),
                last_observed=interactions[-1].timestamp
            )
        
        return None
    
    def _analyze_content_patterns(self, interactions: List[UserInteraction]) -> Optional[BehaviorPattern]:
        """Analyze content-based behavior patterns"""
        if len(interactions) < 3:
            return None
        
        # Analyze content categories
        category_counts = Counter()
        for interaction in interactions:
            content_lower = interaction.content.lower()
            
            for category, keywords in self.content_keywords.items():
                keyword_matches = sum(1 for keyword in keywords if keyword in content_lower)
                if keyword_matches > 0:
                    category_counts[category.value] += keyword_matches
        
        if category_counts:
            total_matches = sum(category_counts.values())
            content_affinity = {
                category: count / total_matches
                for category, count in category_counts.items()
            }
            
            return BehaviorPattern(
                pattern_type="content_preference",
                frequency=1.0,
                time_distribution={},
                content_affinity=content_affinity,
                confidence=min(len(content_affinity) / len(ContentCategory), 1.0),
                last_observed=interactions[-1].timestamp
            )
        
        return None
    
    def _analyze_interaction_patterns_detailed(self, interactions: List[UserInteraction]) -> Optional[BehaviorPattern]:
        """Analyze detailed interaction patterns"""
        if len(interactions) < 5:
            return None
        
        # Analyze interaction type preferences
        type_counts = Counter()
        for interaction in interactions:
            type_counts[interaction.interaction_type.value] += 1
        
        total_interactions = len(interactions)
        type_affinity = {
            interaction_type: count / total_interactions
            for interaction_type, count in type_counts.items()
        }
        
        return BehaviorPattern(
            pattern_type="interaction_preference",
            frequency=1.0,
            time_distribution={},
            content_affinity=type_affinity,
            confidence=min(len(type_affinity) / len(InteractionType), 1.0),
            last_observed=interactions[-1].timestamp
        )
    
    async def get_user_profile(self, user_id: int) -> Optional[UserPreferenceProfile]:
        """Get user preference profile"""
        try:
            # Check cache first
            if user_id in self.user_profiles:
                return self.user_profiles[user_id]
            
            # Try to create profile if not exists
            await self._update_user_profile_if_needed(user_id)
            
            return self.user_profiles.get(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def get_behavior_patterns(self, user_id: int) -> List[BehaviorPattern]:
        """Get user behavior patterns"""
        try:
            if user_id in self.behavior_patterns:
                return self.behavior_patterns[user_id]
            
            # Try to update patterns
            await self._update_user_profile_if_needed(user_id)
            
            return self.behavior_patterns.get(user_id, [])
            
        except Exception as e:
            logger.error(f"Error getting behavior patterns: {e}")
            return []
    
    async def generate_personalization_recommendations(self, user_id: int, 
                                                     content_type: str = "all",
                                                     limit: int = 10) -> List[PersonalizationRecommendation]:
        """Generate personalized recommendations for user"""
        try:
            profile = await self.get_user_profile(user_id)
            if not profile:
                return []
            
            recommendations = []
            
            # Content-based recommendations
            if content_type in ["all", "content"]:
                content_recs = self._generate_content_recommendations(profile, limit)
                recommendations.extend(content_recs)
            
            # Interaction-based recommendations
            if content_type in ["all", "interaction"]:
                interaction_recs = self._generate_interaction_recommendations(profile, limit)
                recommendations.extend(interaction_recs)
            
            # Goal-based recommendations
            if content_type in ["all", "goals"]:
                goal_recs = self._generate_goal_recommendations(profile, limit)
                recommendations.extend(goal_recs)
            
            # Sort by relevance and return top recommendations
            recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _generate_content_recommendations(self, profile: UserPreferenceProfile, 
                                        limit: int) -> List[PersonalizationRecommendation]:
        """Generate content-based recommendations"""
        recommendations = []
        
        # Sort content preferences by strength
        sorted_preferences = sorted(
            profile.content_preferences.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for category, strength in sorted_preferences[:limit//2]:
            if strength > 0.3:  # Only recommend if preference is significant
                recommendation = PersonalizationRecommendation(
                    content_type="content",
                    content_id=f"category_{category.value}",
                    relevance_score=strength,
                    reasoning=f"Based on your interest in {category.value} topics",
                    user_preferences_used=[f"content_preference_{category.value}"],
                    confidence=profile.confidence_score
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_interaction_recommendations(self, profile: UserPreferenceProfile, 
                                            limit: int) -> List[PersonalizationRecommendation]:
        """Generate interaction-based recommendations"""
        recommendations = []
        
        # Analyze interaction patterns
        patterns = profile.interaction_patterns
        
        # Recommend based on peak hours
        if 'peak_hours' in patterns and patterns['peak_hours']:
            peak_hour = max(patterns['peak_hours'].items(), key=lambda x: x[1])[0]
            recommendation = PersonalizationRecommendation(
                content_type="reminder",
                content_id=f"reminder_{peak_hour}",
                relevance_score=0.8,
                reasoning=f"Based on your active hours around {peak_hour}:00",
                user_preferences_used=["peak_hours"],
                confidence=profile.confidence_score
            )
            recommendations.append(recommendation)
        
        # Recommend based on interaction frequency
        if 'frequency' in patterns and patterns['frequency'] > 0:
            if patterns['frequency'] > 5:  # High frequency user
                recommendation = PersonalizationRecommendation(
                    content_type="feature",
                    content_id="advanced_features",
                    relevance_score=0.9,
                    reasoning="Based on your high engagement level",
                    user_preferences_used=["interaction_frequency"],
                    confidence=profile.confidence_score
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_goal_recommendations(self, profile: UserPreferenceProfile, 
                                     limit: int) -> List[PersonalizationRecommendation]:
        """Generate goal-based recommendations"""
        recommendations = []
        
        for goal in profile.health_goals[:limit//2]:
            recommendation = PersonalizationRecommendation(
                content_type="goal",
                content_id=f"goal_{hashlib.md5(goal.encode()).hexdigest()[:8]}",
                relevance_score=0.85,
                reasoning=f"Based on your health goal: {goal[:50]}...",
                user_preferences_used=["health_goals"],
                confidence=profile.confidence_score
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def cleanup_old_data(self, days: int = 90) -> int:
        """Clean up old interaction data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            cleaned_count = 0
            
            # Clean cache
            for user_id in list(self.interaction_cache.keys()):
                original_count = len(self.interaction_cache[user_id])
                self.interaction_cache[user_id] = [
                    interaction for interaction in self.interaction_cache[user_id]
                    if interaction.timestamp >= cutoff_date
                ]
                cleaned_count += original_count - len(self.interaction_cache[user_id])
            
            # Clean database (simplified - would need proper implementation)
            logger.info(f"Cleaned up {cleaned_count} old interactions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0

# Global user modeling backend instance
user_modeling_backend = None

def get_user_modeling_backend() -> UserModelingBackend:
    """Get or create user modeling backend instance"""
    global user_modeling_backend
    if user_modeling_backend is None:
        user_modeling_backend = UserModelingBackend()
    return user_modeling_backend 