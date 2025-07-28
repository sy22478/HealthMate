"""
Enhanced Health Analytics Backend
Comprehensive analytics engine for health trend analysis, pattern recognition, and insights generation
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import statistics
from collections import defaultdict
import numpy as np
from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc

from app.database import get_db
from app.models.enhanced_health_models import (
    UserHealthProfile, HealthMetricsAggregation, EnhancedMedication, 
    EnhancedSymptomLog, HealthMetricsAggregation
)
from app.services.enhanced.data_integration import (
    DataIntegrationService, HealthDataPoint, DataType, DataSourceType
)
from app.exceptions.health_exceptions import HealthDataError, BusinessIntelligenceError
from app.utils.encryption_utils import field_encryption

logger = logging.getLogger(__name__)

class AnalyticsType(str, Enum):
    """Types of health analytics"""
    TREND_ANALYSIS = "trend_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    HEALTH_SCORING = "health_scoring"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    PREDICTIVE_MODELING = "predictive_modeling"

class TrendDirection(str, Enum):
    """Trend direction indicators"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"

class HealthScoreCategory(str, Enum):
    """Health score categories"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    data_type: str
    direction: TrendDirection
    slope: float
    strength: float
    confidence: float
    period_start: datetime
    period_end: datetime
    data_points: int
    seasonal_pattern: Optional[str] = None
    cyclical_pattern: Optional[str] = None

@dataclass
class PatternRecognition:
    """Pattern recognition result"""
    pattern_type: str
    pattern_name: str
    confidence: float
    description: str
    frequency: Optional[str] = None
    triggers: Optional[List[str]] = None
    impact: Optional[str] = None

@dataclass
class HealthScore:
    """Health score result"""
    overall_score: float
    category: HealthScoreCategory
    component_scores: Dict[str, float]
    factors: List[str]
    recommendations: List[str]
    last_updated: datetime

@dataclass
class ComparativeAnalysis:
    """Comparative analysis result"""
    comparison_type: str
    user_percentile: float
    peer_group: str
    differences: Dict[str, float]
    insights: List[str]
    recommendations: List[str]

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_type: str
    risk_level: str
    probability: float
    severity: str
    factors: List[str]
    mitigation_strategies: List[str]
    monitoring_recommendations: List[str]

class HealthAnalyticsEngine:
    """Main health analytics engine"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.data_integration = DataIntegrationService()
        self.analytics_config = self._load_analytics_config()
        self.scoring_weights = self._load_scoring_weights()
    
    def _load_analytics_config(self) -> Dict[str, Any]:
        """Load analytics configuration"""
        return {
            'trend_analysis': {
                'min_data_points': 7,
                'confidence_threshold': 0.7,
                'seasonal_periods': [7, 30, 90],  # days
                'trend_strength_threshold': 0.1
            },
            'pattern_recognition': {
                'min_pattern_length': 3,
                'pattern_confidence_threshold': 0.6,
                'correlation_threshold': 0.5
            },
            'health_scoring': {
                'update_frequency_hours': 24,
                'min_data_completeness': 0.7,
                'score_normalization': True
            },
            'comparative_analysis': {
                'peer_group_size': 100,
                'percentile_bins': [25, 50, 75, 90],
                'age_group_ranges': [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
            },
            'risk_assessment': {
                'risk_thresholds': {
                    'low': 0.3,
                    'medium': 0.6,
                    'high': 0.8
                },
                'assessment_frequency_hours': 12
            }
        }
    
    def _load_scoring_weights(self) -> Dict[str, float]:
        """Load health scoring weights"""
        return {
            'heart_rate': 0.15,
            'blood_pressure': 0.20,
            'steps': 0.10,
            'sleep': 0.15,
            'weight': 0.10,
            'medication_adherence': 0.15,
            'symptom_frequency': 0.10,
            'overall_activity': 0.05
        }
    
    async def run_comprehensive_analytics(self, user_id: int, 
                                        analytics_types: List[AnalyticsType] = None) -> Dict[str, Any]:
        """Run comprehensive health analytics for a user"""
        if analytics_types is None:
            analytics_types = list(AnalyticsType)
        
        results = {}
        
        try:
            # Get user health data
            health_data = await self._get_user_health_data(user_id)
            
            if not health_data:
                logger.warning(f"No health data found for user {user_id}")
                return results
            
            # Run requested analytics
            for analytics_type in analytics_types:
                try:
                    if analytics_type == AnalyticsType.TREND_ANALYSIS:
                        results['trends'] = await self._analyze_trends(user_id, health_data)
                    
                    elif analytics_type == AnalyticsType.PATTERN_RECOGNITION:
                        results['patterns'] = await self._recognize_patterns(user_id, health_data)
                    
                    elif analytics_type == AnalyticsType.HEALTH_SCORING:
                        results['health_score'] = await self._calculate_health_score(user_id, health_data)
                    
                    elif analytics_type == AnalyticsType.COMPARATIVE_ANALYSIS:
                        results['comparative'] = await self._perform_comparative_analysis(user_id, health_data)
                    
                    elif analytics_type == AnalyticsType.RISK_ASSESSMENT:
                        results['risk_assessment'] = await self._assess_health_risks(user_id, health_data)
                    
                    elif analytics_type == AnalyticsType.PREDICTIVE_MODELING:
                        results['predictions'] = await self._generate_predictions(user_id, health_data)
                    
                except Exception as e:
                    logger.error(f"Error running {analytics_type}: {str(e)}")
                    results[analytics_type.value] = {'error': str(e)}
            
        except Exception as e:
            logger.error(f"Error in comprehensive analytics: {str(e)}")
            raise AnalyticsError(f"Analytics processing failed: {str(e)}")
        
        return results
    
    async def _get_user_health_data(self, user_id: int) -> List[HealthDataPoint]:
        """Get comprehensive health data for analytics"""
        # Get data from multiple sources and time periods
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)  # 3 months of data
        
        data_types = [
            DataType.HEART_RATE, DataType.BLOOD_PRESSURE, DataType.STEPS,
            DataType.SLEEP, DataType.WEIGHT, DataType.BLOOD_GLUCOSE
        ]
        
        sources = [DataSourceType.FITBIT, DataSourceType.MANUAL_ENTRY]
        
        try:
            data_points = await self.data_integration.fetch_user_health_data(
                user_id, data_types, sources, start_date, end_date
            )
            
            # Also get aggregated metrics
            aggregated_data = self._get_aggregated_metrics(user_id, start_date, end_date)
            
            return data_points + aggregated_data
            
        except Exception as e:
            logger.error(f"Error fetching health data: {str(e)}")
            return []
    
    def _get_aggregated_metrics(self, user_id: int, start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Get aggregated health metrics from database"""
        try:
            aggregations = self.db.query(HealthMetricsAggregation).filter(
                and_(
                    HealthMetricsAggregation.health_profile_id == user_id,
                    HealthMetricsAggregation.period_start >= start_date,
                    HealthMetricsAggregation.period_end <= end_date
                )
            ).all()
            
            data_points = []
            for agg in aggregations:
                # Convert aggregated metrics to data points
                if agg.avg_heart_rate:
                    data_points.append(HealthDataPoint(
                        user_id=user_id,
                        data_type=DataType.HEART_RATE,
                        value=agg.avg_heart_rate,
                        unit='bpm',
                        timestamp=agg.period_start,
                        source=DataSourceType.MANUAL_ENTRY,
                        confidence=0.9
                    ))
                
                if agg.total_steps:
                    data_points.append(HealthDataPoint(
                        user_id=user_id,
                        data_type=DataType.STEPS,
                        value=agg.total_steps,
                        unit='steps',
                        timestamp=agg.period_start,
                        source=DataSourceType.MANUAL_ENTRY,
                        confidence=0.9
                    ))
                
                # Add more aggregated metrics as needed
            
            return data_points
            
        except Exception as e:
            logger.error(f"Error fetching aggregated metrics: {str(e)}")
            return []
    
    async def _analyze_trends(self, user_id: int, health_data: List[HealthDataPoint]) -> List[TrendAnalysis]:
        """Analyze trends in health data"""
        trends = []
        
        # Group data by type
        by_type = defaultdict(list)
        for point in health_data:
            by_type[point.data_type].append(point)
        
        for data_type, points in by_type.items():
            if len(points) < self.analytics_config['trend_analysis']['min_data_points']:
                continue
            
            # Sort by timestamp
            sorted_points = sorted(points, key=lambda p: p.timestamp)
            
            # Calculate trend
            trend = self._calculate_trend(data_type, sorted_points)
            if trend:
                trends.append(trend)
        
        return trends
    
    def _calculate_trend(self, data_type: DataType, points: List[HealthDataPoint]) -> Optional[TrendAnalysis]:
        """Calculate trend for a specific data type"""
        if len(points) < 3:
            return None
        
        # Extract values and timestamps
        values = [p.value for p in points if isinstance(p.value, (int, float))]
        timestamps = [p.timestamp for p in points if isinstance(p.value, (int, float))]
        
        if len(values) < 3:
            return None
        
        # Convert timestamps to numeric values for regression
        time_numeric = [(ts - timestamps[0]).total_seconds() / 86400 for ts in timestamps]  # Days since first point
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, values)
        
        # Calculate confidence
        confidence = abs(r_value) if not np.isnan(r_value) else 0.0
        
        # Determine direction
        if abs(slope) < self.analytics_config['trend_analysis']['trend_strength_threshold']:
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Check for seasonal patterns
        seasonal_pattern = self._detect_seasonal_pattern(values, timestamps)
        
        # Check for cyclical patterns
        cyclical_pattern = self._detect_cyclical_pattern(values, timestamps)
        
        return TrendAnalysis(
            data_type=data_type.value,
            direction=direction,
            slope=slope,
            strength=abs(slope),
            confidence=confidence,
            period_start=timestamps[0],
            period_end=timestamps[-1],
            data_points=len(values),
            seasonal_pattern=seasonal_pattern,
            cyclical_pattern=cyclical_pattern
        )
    
    def _detect_seasonal_pattern(self, values: List[float], timestamps: List[datetime]) -> Optional[str]:
        """Detect seasonal patterns in data"""
        if len(values) < 30:  # Need at least 30 days
            return None
        
        # Simple seasonal detection based on weekly patterns
        weekly_avgs = defaultdict(list)
        for i, ts in enumerate(timestamps):
            day_of_week = ts.weekday()
            weekly_avgs[day_of_week].append(values[i])
        
        # Calculate variance in weekly patterns
        weekly_means = [statistics.mean(weekly_avgs[day]) for day in range(7) if weekly_avgs[day]]
        
        if len(weekly_means) == 7:
            variance = statistics.variance(weekly_means)
            if variance > 0.1:  # Significant weekly variation
                return "weekly"
        
        return None
    
    def _detect_cyclical_pattern(self, values: List[float], timestamps: List[datetime]) -> Optional[str]:
        """Detect cyclical patterns in data"""
        if len(values) < 20:
            return None
        
        # Simple cyclical detection using autocorrelation
        try:
            # Calculate autocorrelation
            autocorr = np.correlate(values, values, mode='full')
            autocorr = autocorr[len(values)-1:]
            
            # Find peaks in autocorrelation
            peaks = []
            for i in range(1, len(autocorr)-1):
                if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                    peaks.append(i)
            
            if peaks:
                # Check if there's a consistent cycle
                cycle_lengths = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
                if cycle_lengths:
                    avg_cycle = statistics.mean(cycle_lengths)
                    if 3 <= avg_cycle <= 30:  # Reasonable cycle length
                        return f"{avg_cycle:.0f}_day_cycle"
        
        except Exception as e:
            logger.warning(f"Error detecting cyclical pattern: {str(e)}")
        
        return None
    
    async def _recognize_patterns(self, user_id: int, health_data: List[HealthDataPoint]) -> List[PatternRecognition]:
        """Recognize patterns in health data"""
        patterns = []
        
        # Group data by type
        by_type = defaultdict(list)
        for point in health_data:
            by_type[point.data_type].append(point)
        
        for data_type, points in by_type.items():
            if len(points) < self.analytics_config['pattern_recognition']['min_pattern_length']:
                continue
            
            # Sort by timestamp
            sorted_points = sorted(points, key=lambda p: p.timestamp)
            
            # Detect various patterns
            type_patterns = self._detect_patterns_for_type(data_type, sorted_points)
            patterns.extend(type_patterns)
        
        # Cross-correlation patterns
        correlation_patterns = self._detect_correlation_patterns(by_type)
        patterns.extend(correlation_patterns)
        
        return patterns
    
    def _detect_patterns_for_type(self, data_type: DataType, points: List[HealthDataPoint]) -> List[PatternRecognition]:
        """Detect patterns for a specific data type"""
        patterns = []
        
        if len(points) < 3:
            return patterns
        
        values = [p.value for p in points if isinstance(p.value, (int, float))]
        timestamps = [p.timestamp for p in points if isinstance(p.value, (int, float))]
        
        if len(values) < 3:
            return patterns
        
        # Detect spikes
        spike_patterns = self._detect_spike_patterns(values, timestamps, data_type)
        patterns.extend(spike_patterns)
        
        # Detect trends
        trend_patterns = self._detect_trend_patterns(values, timestamps, data_type)
        patterns.extend(trend_patterns)
        
        # Detect cycles
        cycle_patterns = self._detect_cycle_patterns(values, timestamps, data_type)
        patterns.extend(cycle_patterns)
        
        return patterns
    
    def _detect_spike_patterns(self, values: List[float], timestamps: List[datetime], 
                             data_type: DataType) -> List[PatternRecognition]:
        """Detect spike patterns in data"""
        patterns = []
        
        if len(values) < 5:
            return patterns
        
        # Calculate moving average
        window_size = min(5, len(values) // 2)
        moving_avg = []
        for i in range(len(values)):
            start = max(0, i - window_size)
            end = min(len(values), i + window_size + 1)
            moving_avg.append(statistics.mean(values[start:end]))
        
        # Detect spikes
        threshold = 2.0  # Standard deviations
        for i in range(1, len(values) - 1):
            if moving_avg[i] > 0:
                z_score = abs(values[i] - moving_avg[i]) / statistics.stdev(values)
                if z_score > threshold:
                    patterns.append(PatternRecognition(
                        pattern_type="spike",
                        pattern_name=f"{data_type.value}_spike",
                        confidence=min(z_score / 4.0, 1.0),
                        description=f"Unusual {data_type.value} spike detected",
                        frequency="occasional",
                        triggers=["stress", "activity", "medication"],
                        impact="temporary"
                    ))
        
        return patterns
    
    def _detect_trend_patterns(self, values: List[float], timestamps: List[datetime], 
                             data_type: DataType) -> List[PatternRecognition]:
        """Detect trend patterns in data"""
        patterns = []
        
        if len(values) < 7:
            return patterns
        
        # Calculate trend using linear regression
        time_numeric = [(ts - timestamps[0]).total_seconds() / 86400 for ts in timestamps]
        slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, values)
        
        if abs(r_value) > self.analytics_config['pattern_recognition']['correlation_threshold']:
            if slope > 0:
                patterns.append(PatternRecognition(
                    pattern_type="trend",
                    pattern_name=f"{data_type.value}_increasing_trend",
                    confidence=abs(r_value),
                    description=f"Consistent increase in {data_type.value}",
                    frequency="continuous",
                    triggers=["lifestyle_change", "aging", "condition_progression"],
                    impact="long_term"
                ))
            else:
                patterns.append(PatternRecognition(
                    pattern_type="trend",
                    pattern_name=f"{data_type.value}_decreasing_trend",
                    confidence=abs(r_value),
                    description=f"Consistent decrease in {data_type.value}",
                    frequency="continuous",
                    triggers=["treatment_effectiveness", "lifestyle_improvement"],
                    impact="long_term"
                ))
        
        return patterns
    
    def _detect_cycle_patterns(self, values: List[float], timestamps: List[datetime], 
                             data_type: DataType) -> List[PatternRecognition]:
        """Detect cycle patterns in data"""
        patterns = []
        
        if len(values) < 14:
            return patterns
        
        # Simple cycle detection
        # Check for weekly cycles
        weekly_avgs = defaultdict(list)
        for i, ts in enumerate(timestamps):
            day_of_week = ts.weekday()
            weekly_avgs[day_of_week].append(values[i])
        
        weekly_means = [statistics.mean(weekly_avgs[day]) for day in range(7) if weekly_avgs[day]]
        
        if len(weekly_means) == 7:
            variance = statistics.variance(weekly_means)
            if variance > 0.1:
                patterns.append(PatternRecognition(
                    pattern_type="cycle",
                    pattern_name=f"{data_type.value}_weekly_cycle",
                    confidence=min(variance, 1.0),
                    description=f"Weekly cycle detected in {data_type.value}",
                    frequency="weekly",
                    triggers=["work_schedule", "weekend_activities"],
                    impact="predictable"
                ))
        
        return patterns
    
    def _detect_correlation_patterns(self, by_type: Dict[DataType, List[HealthDataPoint]]) -> List[PatternRecognition]:
        """Detect correlation patterns between different data types"""
        patterns = []
        
        data_types = list(by_type.keys())
        if len(data_types) < 2:
            return patterns
        
        # Create time-aligned data series
        for i, type1 in enumerate(data_types):
            for type2 in data_types[i+1:]:
                correlation = self._calculate_correlation(by_type[type1], by_type[type2])
                
                if abs(correlation) > self.analytics_config['pattern_recognition']['correlation_threshold']:
                    direction = "positive" if correlation > 0 else "negative"
                    patterns.append(PatternRecognition(
                        pattern_type="correlation",
                        pattern_name=f"{type1.value}_{type2.value}_correlation",
                        confidence=abs(correlation),
                        description=f"{direction.capitalize()} correlation between {type1.value} and {type2.value}",
                        frequency="continuous",
                        triggers=["physiological_relationship", "lifestyle_factors"],
                        impact="interdependent"
                    ))
        
        return patterns
    
    def _calculate_correlation(self, points1: List[HealthDataPoint], points2: List[HealthDataPoint]) -> float:
        """Calculate correlation between two data series"""
        try:
            # Align data by time
            aligned_data = self._align_data_series(points1, points2)
            
            if len(aligned_data) < 3:
                return 0.0
            
            values1 = [d[0] for d in aligned_data]
            values2 = [d[1] for d in aligned_data]
            
            correlation, _ = stats.pearsonr(values1, values2)
            return correlation if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating correlation: {str(e)}")
            return 0.0
    
    def _align_data_series(self, points1: List[HealthDataPoint], points2: List[HealthDataPoint]) -> List[Tuple[float, float]]:
        """Align two data series by time"""
        # Create time-indexed dictionaries
        data1 = {p.timestamp: p.value for p in points1 if isinstance(p.value, (int, float))}
        data2 = {p.timestamp: p.value for p in points2 if isinstance(p.value, (int, float))}
        
        # Find common timestamps
        common_times = set(data1.keys()) & set(data2.keys())
        
        # Return aligned data
        return [(data1[ts], data2[ts]) for ts in sorted(common_times)]
    
    async def _calculate_health_score(self, user_id: int, health_data: List[HealthDataPoint]) -> HealthScore:
        """Calculate comprehensive health score"""
        component_scores = {}
        factors = []
        recommendations = []
        
        # Calculate scores for each component
        for data_type, weight in self.scoring_weights.items():
            try:
                score = await self._calculate_component_score(data_type, health_data)
                component_scores[data_type] = score
                
                # Add factors and recommendations based on score
                if score < 0.6:
                    factors.append(f"Low {data_type.replace('_', ' ')} score")
                    recommendations.append(f"Improve {data_type.replace('_', ' ')} through lifestyle changes")
                
            except Exception as e:
                logger.warning(f"Error calculating {data_type} score: {str(e)}")
                component_scores[data_type] = 0.5  # Default score
        
        # Calculate overall score
        overall_score = sum(score * self.scoring_weights[component] 
                           for component, score in component_scores.items())
        
        # Determine category
        if overall_score >= 0.9:
            category = HealthScoreCategory.EXCELLENT
        elif overall_score >= 0.8:
            category = HealthScoreCategory.GOOD
        elif overall_score >= 0.7:
            category = HealthScoreCategory.FAIR
        elif overall_score >= 0.6:
            category = HealthScoreCategory.POOR
        else:
            category = HealthScoreCategory.CRITICAL
        
        return HealthScore(
            overall_score=overall_score,
            category=category,
            component_scores=component_scores,
            factors=factors,
            recommendations=recommendations,
            last_updated=datetime.utcnow()
        )
    
    async def _calculate_component_score(self, component: str, health_data: List[HealthDataPoint]) -> float:
        """Calculate score for a specific health component"""
        # Filter data for this component
        component_data = [p for p in health_data if p.data_type.value == component]
        
        if not component_data:
            return 0.5  # Default score if no data
        
        # Component-specific scoring logic
        if component == 'heart_rate':
            return self._score_heart_rate(component_data)
        elif component == 'blood_pressure':
            return self._score_blood_pressure(component_data)
        elif component == 'steps':
            return self._score_steps(component_data)
        elif component == 'sleep':
            return self._score_sleep(component_data)
        elif component == 'weight':
            return self._score_weight(component_data)
        else:
            return 0.7  # Default score
    
    def _score_heart_rate(self, data_points: List[HealthDataPoint]) -> float:
        """Score heart rate data"""
        values = [p.value for p in data_points if isinstance(p.value, (int, float))]
        
        if not values:
            return 0.5
        
        avg_hr = statistics.mean(values)
        
        # Score based on resting heart rate ranges
        if 60 <= avg_hr <= 100:
            return 0.9
        elif 50 <= avg_hr < 60 or 100 < avg_hr <= 110:
            return 0.7
        elif 40 <= avg_hr < 50 or 110 < avg_hr <= 120:
            return 0.5
        else:
            return 0.3
    
    def _score_blood_pressure(self, data_points: List[HealthDataPoint]) -> float:
        """Score blood pressure data"""
        # This would need to handle dict values for BP
        return 0.7  # Placeholder
    
    def _score_steps(self, data_points: List[HealthDataPoint]) -> float:
        """Score steps data"""
        values = [p.value for p in data_points if isinstance(p.value, (int, float))]
        
        if not values:
            return 0.5
        
        avg_steps = statistics.mean(values)
        
        # Score based on daily step count
        if avg_steps >= 10000:
            return 0.9
        elif avg_steps >= 7500:
            return 0.8
        elif avg_steps >= 5000:
            return 0.7
        elif avg_steps >= 2500:
            return 0.6
        else:
            return 0.4
    
    def _score_sleep(self, data_points: List[HealthDataPoint]) -> float:
        """Score sleep data"""
        values = [p.value for p in data_points if isinstance(p.value, (int, float))]
        
        if not values:
            return 0.5
        
        # Convert to hours if in minutes
        hours = [v / 60 if v > 24 else v for v in values]
        avg_sleep = statistics.mean(hours)
        
        # Score based on sleep duration
        if 7 <= avg_sleep <= 9:
            return 0.9
        elif 6 <= avg_sleep < 7 or 9 < avg_sleep <= 10:
            return 0.7
        elif 5 <= avg_sleep < 6 or 10 < avg_sleep <= 11:
            return 0.5
        else:
            return 0.3
    
    def _score_weight(self, data_points: List[HealthDataPoint]) -> float:
        """Score weight data"""
        # This would need BMI calculation and health profile data
        return 0.7  # Placeholder
    
    async def _perform_comparative_analysis(self, user_id: int, health_data: List[HealthDataPoint]) -> List[ComparativeAnalysis]:
        """Perform comparative analysis against peer groups"""
        comparisons = []
        
        try:
            # Get user profile for peer group matching
            user_profile = self.db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id
            ).first()
            
            if not user_profile:
                return comparisons
            
            # Get peer group data
            peer_data = await self._get_peer_group_data(user_profile)
            
            # Compare each health metric
            for data_type in set(p.data_type for p in health_data):
                comparison = await self._compare_metric(user_id, data_type, health_data, peer_data, user_profile)
                if comparison:
                    comparisons.append(comparison)
            
        except Exception as e:
            logger.error(f"Error in comparative analysis: {str(e)}")
        
        return comparisons
    
    async def _get_peer_group_data(self, user_profile: UserHealthProfile) -> Dict[str, List[float]]:
        """Get peer group data for comparison"""
        # This would typically query a large dataset of users
        # For now, return mock data
        return {
            'heart_rate': [65, 70, 75, 80, 85, 90, 95],
            'steps': [5000, 7500, 10000, 12500, 15000],
            'sleep': [6.5, 7.0, 7.5, 8.0, 8.5, 9.0],
            'weight': [60, 65, 70, 75, 80, 85, 90]
        }
    
    async def _compare_metric(self, user_id: int, data_type: DataType, health_data: List[HealthDataPoint], 
                            peer_data: Dict[str, List[float]], user_profile: UserHealthProfile) -> Optional[ComparativeAnalysis]:
        """Compare a specific metric against peer group"""
        # Get user's average for this metric
        user_values = [p.value for p in health_data if p.data_type == data_type and isinstance(p.value, (int, float))]
        
        if not user_values:
            return None
        
        user_avg = statistics.mean(user_values)
        peer_values = peer_data.get(data_type.value, [])
        
        if not peer_values:
            return None
        
        # Calculate percentile
        percentile = self._calculate_percentile(user_avg, peer_values)
        
        # Calculate differences
        peer_avg = statistics.mean(peer_values)
        differences = {
            'vs_peer_average': user_avg - peer_avg,
            'percentile': percentile
        }
        
        # Generate insights
        insights = []
        if percentile > 75:
            insights.append(f"Your {data_type.value} is above average for your peer group")
        elif percentile < 25:
            insights.append(f"Your {data_type.value} is below average for your peer group")
        else:
            insights.append(f"Your {data_type.value} is within normal range for your peer group")
        
        # Generate recommendations
        recommendations = []
        if percentile < 25:
            recommendations.append(f"Consider improving your {data_type.value} through lifestyle changes")
        elif percentile > 90:
            recommendations.append(f"Your {data_type.value} is excellent - maintain current habits")
        
        return ComparativeAnalysis(
            comparison_type=f"{data_type.value}_peer_comparison",
            user_percentile=percentile,
            peer_group="age_gender_matched",
            differences=differences,
            insights=insights,
            recommendations=recommendations
        )
    
    def _calculate_percentile(self, value: float, data: List[float]) -> float:
        """Calculate percentile of a value in a dataset"""
        if not data:
            return 50.0
        
        sorted_data = sorted(data)
        position = 0
        
        for i, data_point in enumerate(sorted_data):
            if value <= data_point:
                position = i
                break
        else:
            position = len(sorted_data)
        
        percentile = (position / len(sorted_data)) * 100
        return percentile
    
    async def _assess_health_risks(self, user_id: int, health_data: List[HealthDataPoint]) -> List[RiskAssessment]:
        """Assess health risks based on data patterns"""
        risks = []
        
        try:
            # Cardiovascular risk assessment
            cv_risk = await self._assess_cardiovascular_risk(user_id, health_data)
            if cv_risk:
                risks.append(cv_risk)
            
            # Diabetes risk assessment
            diabetes_risk = await self._assess_diabetes_risk(user_id, health_data)
            if diabetes_risk:
                risks.append(diabetes_risk)
            
            # Mental health risk assessment
            mental_health_risk = await self._assess_mental_health_risk(user_id, health_data)
            if mental_health_risk:
                risks.append(mental_health_risk)
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {str(e)}")
        
        return risks
    
    async def _assess_cardiovascular_risk(self, user_id: int, health_data: List[HealthDataPoint]) -> Optional[RiskAssessment]:
        """Assess cardiovascular risk"""
        # Get relevant data
        heart_rate_data = [p for p in health_data if p.data_type == DataType.HEART_RATE]
        blood_pressure_data = [p for p in health_data if p.data_type == DataType.BLOOD_PRESSURE]
        
        risk_factors = []
        risk_score = 0.0
        
        # Heart rate analysis
        if heart_rate_data:
            hr_values = [p.value for p in heart_rate_data if isinstance(p.value, (int, float))]
            if hr_values:
                avg_hr = statistics.mean(hr_values)
                if avg_hr > 100:
                    risk_factors.append("Elevated resting heart rate")
                    risk_score += 0.3
                elif avg_hr > 80:
                    risk_factors.append("Above-normal heart rate")
                    risk_score += 0.1
        
        # Blood pressure analysis (placeholder)
        if blood_pressure_data:
            risk_factors.append("Blood pressure monitoring needed")
            risk_score += 0.2
        
        if risk_score > 0:
            # Determine risk level
            if risk_score >= self.analytics_config['risk_assessment']['risk_thresholds']['high']:
                risk_level = "high"
            elif risk_score >= self.analytics_config['risk_assessment']['risk_thresholds']['medium']:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return RiskAssessment(
                risk_type="cardiovascular",
                risk_level=risk_level,
                probability=risk_score,
                severity="moderate",
                factors=risk_factors,
                mitigation_strategies=[
                    "Regular cardiovascular exercise",
                    "Blood pressure monitoring",
                    "Heart-healthy diet"
                ],
                monitoring_recommendations=[
                    "Daily heart rate monitoring",
                    "Weekly blood pressure checks",
                    "Annual cardiovascular screening"
                ]
            )
        
        return None
    
    async def _assess_diabetes_risk(self, user_id: int, health_data: List[HealthDataPoint]) -> Optional[RiskAssessment]:
        """Assess diabetes risk"""
        # Placeholder implementation
        return None
    
    async def _assess_mental_health_risk(self, user_id: int, health_data: List[HealthDataPoint]) -> Optional[RiskAssessment]:
        """Assess mental health risk"""
        # Placeholder implementation
        return None
    
    async def _generate_predictions(self, user_id: int, health_data: List[HealthDataPoint]) -> Dict[str, Any]:
        """Generate health predictions"""
        predictions = {}
        
        try:
            # Simple trend-based predictions
            for data_type in set(p.data_type for p in health_data):
                prediction = await self._predict_metric_trend(user_id, data_type, health_data)
                if prediction:
                    predictions[data_type.value] = prediction
            
        except Exception as e:
            logger.error(f"Error generating predictions: {str(e)}")
        
        return predictions
    
    async def _predict_metric_trend(self, user_id: int, data_type: DataType, 
                                  health_data: List[HealthDataPoint]) -> Optional[Dict[str, Any]]:
        """Predict trend for a specific metric"""
        # Filter data for this type
        type_data = [p for p in health_data if p.data_type == data_type]
        
        if len(type_data) < 7:
            return None
        
        # Sort by timestamp
        sorted_data = sorted(type_data, key=lambda p: p.timestamp)
        values = [p.value for p in sorted_data if isinstance(p.value, (int, float))]
        timestamps = [p.timestamp for p in sorted_data if isinstance(p.value, (int, float))]
        
        if len(values) < 7:
            return None
        
        # Simple linear prediction
        time_numeric = [(ts - timestamps[0]).total_seconds() / 86400 for ts in timestamps]
        slope, intercept, r_value, p_value, std_err = stats.linregress(time_numeric, values)
        
        # Predict next 30 days
        future_days = 30
        future_time = time_numeric[-1] + future_days
        predicted_value = slope * future_time + intercept
        
        return {
            'current_value': values[-1],
            'predicted_value': predicted_value,
            'trend_direction': 'increasing' if slope > 0 else 'decreasing',
            'confidence': abs(r_value),
            'prediction_horizon_days': future_days
        }

# Global analytics engine instance
health_analytics_engine = None

def get_health_analytics_engine(db_session: Session) -> HealthAnalyticsEngine:
    """Get or create health analytics engine instance"""
    global health_analytics_engine
    if health_analytics_engine is None:
        health_analytics_engine = HealthAnalyticsEngine(db_session)
    return health_analytics_engine 