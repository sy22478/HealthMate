"""
Enhanced Data Integration Services
Comprehensive framework for external health API integrations and data processing
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import time
from abc import ABC, abstractmethod

from app.exceptions.external_api_exceptions import ExternalAPIError, APIError
from app.utils.encryption_utils import field_encryption
from app.models.enhanced_health_models import UserHealthProfile, HealthMetricsAggregation

logger = logging.getLogger(__name__)

class DataSourceType(str, Enum):
    """Supported data source types"""
    FITBIT = "fitbit"
    APPLE_HEALTH = "apple_health"
    GOOGLE_FIT = "google_fit"
    WITHINGS = "withings"
    OURA = "oura"
    GARMIN = "garmin"
    SAMSUNG_HEALTH = "samsung_health"
    CUSTOM_API = "custom_api"
    MANUAL_ENTRY = "manual_entry"

class DataType(str, Enum):
    """Supported health data types"""
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"
    STEPS = "steps"
    SLEEP = "sleep"
    WEIGHT = "weight"
    BLOOD_GLUCOSE = "blood_glucose"
    OXYGEN_SATURATION = "oxygen_saturation"
    TEMPERATURE = "temperature"
    ACTIVITY = "activity"
    NUTRITION = "nutrition"
    MEDICATION = "medication"
    SYMPTOMS = "symptoms"

@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    source_type: DataSourceType
    api_key: str
    api_secret: str
    base_url: str
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 5
    enabled: bool = True
    custom_headers: Optional[Dict[str, str]] = None
    custom_params: Optional[Dict[str, Any]] = None

@dataclass
class HealthDataPoint:
    """Standardized health data point"""
    user_id: int
    data_type: DataType
    value: Union[float, int, str, Dict[str, Any]]
    timestamp: datetime
    source: DataSourceType
    unit: Optional[str] = None
    source_id: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None

class BaseDataProvider(ABC):
    """Abstract base class for data providers"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0
        self.request_count = 0
        self.rate_limit_reset_time = time.time() + 60
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time > self.rate_limit_reset_time:
            self.request_count = 0
            self.rate_limit_reset_time = current_time + 60
        
        # Check if we're at the limit
        if self.request_count >= self.config.rate_limit_per_minute:
            sleep_time = self.rate_limit_reset_time - current_time
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                self.request_count = 0
                self.rate_limit_reset_time = time.time() + 60
        
        # Ensure minimum delay between requests
        time_since_last = current_time - self.last_request_time
        min_delay = 60.0 / self.config.rate_limit_per_minute
        if time_since_last < min_delay:
            await asyncio.sleep(min_delay - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with retry logic and error handling"""
        await self._rate_limit_check()
        
        headers = kwargs.get('headers', {})
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)
        kwargs['headers'] = headers
        
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    if response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', self.config.retry_delay_seconds))
                        logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    if response.status >= 400:
                        error_text = await response.text()
                        raise APIError(
                            f"API request failed with status {response.status}: {error_text}",
                            api_name=self.config.source_type.value,
                            response_status=response.status,
                            response_body=error_text
                        )
                    
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                if attempt == self.config.retry_attempts - 1:
                    raise ExternalAPIError(f"Connection error after {self.config.retry_attempts} attempts: {str(e)}")
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                await asyncio.sleep(self.config.retry_delay_seconds * (attempt + 1))
        
        raise ExternalAPIError("All retry attempts failed")
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the data source"""
        pass
    
    @abstractmethod
    async def fetch_health_data(self, user_id: int, data_types: List[DataType], 
                              start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch health data from the source"""
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: Dict[str, Any], data_type: DataType) -> HealthDataPoint:
        """Normalize raw data to standard format"""
        pass

class FitbitDataProvider(BaseDataProvider):
    """Fitbit API data provider"""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.access_token = None
        self.refresh_token = None
    
    async def authenticate(self) -> bool:
        """Authenticate with Fitbit API"""
        try:
            # Implementation would include OAuth2 flow
            # For now, assuming tokens are provided in config
            self.access_token = self.config.api_key
            self.refresh_token = self.config.api_secret
            return True
        except Exception as e:
            logger.error(f"Fitbit authentication failed: {str(e)}")
            return False
    
    async def fetch_health_data(self, user_id: int, data_types: List[DataType], 
                              start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch health data from Fitbit"""
        if not await self.authenticate():
            raise ExternalAPIError("Failed to authenticate with Fitbit")
        
        data_points = []
        
        for data_type in data_types:
            try:
                if data_type == DataType.HEART_RATE:
                    data_points.extend(await self._fetch_heart_rate(user_id, start_date, end_date))
                elif data_type == DataType.STEPS:
                    data_points.extend(await self._fetch_steps(user_id, start_date, end_date))
                elif data_type == DataType.SLEEP:
                    data_points.extend(await self._fetch_sleep(user_id, start_date, end_date))
                elif data_type == DataType.WEIGHT:
                    data_points.extend(await self._fetch_weight(user_id, start_date, end_date))
                # Add more data types as needed
                
            except Exception as e:
                logger.error(f"Failed to fetch {data_type} from Fitbit: {str(e)}")
                continue
        
        return data_points
    
    async def _fetch_heart_rate(self, user_id: int, start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch heart rate data from Fitbit"""
        url = f"{self.config.base_url}/1/user/-/activities/heart/date/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}.json"
        
        response = await self._make_request(
            'GET', 
            url,
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        data_points = []
        for day_data in response.get('activities-heart', []):
            date = datetime.strptime(day_data['dateTime'], '%Y-%m-%d')
            for zone in day_data.get('value', {}).get('heartRateZones', []):
                data_points.append(HealthDataPoint(
                    user_id=user_id,
                    data_type=DataType.HEART_RATE,
                    value=zone.get('maxHR', 0),
                    unit='bpm',
                    timestamp=date,
                    source=DataSourceType.FITBIT,
                    confidence=0.9,
                    metadata={'zone': zone.get('name', 'unknown')}
                ))
        
        return data_points
    
    async def _fetch_steps(self, user_id: int, start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch steps data from Fitbit"""
        url = f"{self.config.base_url}/1/user/-/activities/steps/date/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}.json"
        
        response = await self._make_request(
            'GET', 
            url,
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        data_points = []
        for day_data in response.get('activities-steps', []):
            data_points.append(HealthDataPoint(
                user_id=user_id,
                data_type=DataType.STEPS,
                value=int(day_data.get('value', 0)),
                unit='steps',
                timestamp=datetime.strptime(day_data['dateTime'], '%Y-%m-%d'),
                source=DataSourceType.FITBIT,
                confidence=0.95
            ))
        
        return data_points
    
    async def _fetch_sleep(self, user_id: int, start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch sleep data from Fitbit"""
        url = f"{self.config.base_url}/1.2/user/-/sleep/date/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}.json"
        
        response = await self._make_request(
            'GET', 
            url,
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        data_points = []
        for sleep_data in response.get('sleep', []):
            data_points.append(HealthDataPoint(
                user_id=user_id,
                data_type=DataType.SLEEP,
                value=sleep_data.get('duration', 0) / 1000 / 60,  # Convert to minutes
                unit='minutes',
                timestamp=datetime.strptime(sleep_data['dateOfSleep'], '%Y-%m-%d'),
                source=DataSourceType.FITBIT,
                confidence=0.9,
                metadata={
                    'sleep_efficiency': sleep_data.get('efficiency', 0),
                    'sleep_stages': sleep_data.get('levels', {}).get('summary', {})
                }
            ))
        
        return data_points
    
    async def _fetch_weight(self, user_id: int, start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch weight data from Fitbit"""
        url = f"{self.config.base_url}/1/user/-/body/log/weight/date/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}.json"
        
        response = await self._make_request(
            'GET', 
            url,
            headers={'Authorization': f'Bearer {self.access_token}'}
        )
        
        data_points = []
        for weight_data in response.get('weight', []):
            data_points.append(HealthDataPoint(
                user_id=user_id,
                data_type=DataType.WEIGHT,
                value=weight_data.get('weight', 0),
                unit='kg',
                timestamp=datetime.strptime(weight_data['date'], '%Y-%m-%d'),
                source=DataSourceType.FITBIT,
                confidence=0.95,
                metadata={'bmi': weight_data.get('bmi', 0)}
            ))
        
        return data_points
    
    def normalize_data(self, raw_data: Dict[str, Any], data_type: DataType) -> HealthDataPoint:
        """Normalize Fitbit data to standard format"""
        # Implementation would convert Fitbit-specific data to standard format
        pass

class AppleHealthDataProvider(BaseDataProvider):
    """Apple HealthKit data provider"""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        # Apple Health integration would require HealthKit framework
        # This is a placeholder implementation
    
    async def authenticate(self) -> bool:
        """Authenticate with Apple Health"""
        # Apple Health authentication is handled by the device
        return True
    
    async def fetch_health_data(self, user_id: int, data_types: List[DataType], 
                              start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch health data from Apple Health"""
        # This would require HealthKit integration
        # For now, return empty list
        return []
    
    def normalize_data(self, raw_data: Dict[str, Any], data_type: DataType) -> HealthDataPoint:
        """Normalize Apple Health data to standard format"""
        pass

class DataIntegrationService:
    """Main service for managing data integrations"""
    
    def __init__(self):
        self.providers: Dict[DataSourceType, BaseDataProvider] = {}
        self.data_cache: Dict[str, List[HealthDataPoint]] = {}
        self.cache_ttl = 300  # 5 minutes
    
    def register_provider(self, provider: BaseDataProvider):
        """Register a data provider"""
        self.providers[provider.config.source_type] = provider
        logger.info(f"Registered data provider: {provider.config.source_type}")
    
    async def fetch_user_health_data(self, user_id: int, data_types: List[DataType], 
                                   sources: List[DataSourceType], 
                                   start_date: datetime, end_date: datetime) -> List[HealthDataPoint]:
        """Fetch health data from multiple sources"""
        all_data_points = []
        
        for source_type in sources:
            if source_type not in self.providers:
                logger.warning(f"No provider registered for source: {source_type}")
                continue
            
            provider = self.providers[source_type]
            if not provider.config.enabled:
                logger.info(f"Provider {source_type} is disabled, skipping")
                continue
            
            try:
                async with provider as p:
                    data_points = await p.fetch_health_data(user_id, data_types, start_date, end_date)
                    all_data_points.extend(data_points)
                    logger.info(f"Fetched {len(data_points)} data points from {source_type}")
                    
            except Exception as e:
                logger.error(f"Failed to fetch data from {source_type}: {str(e)}")
                continue
        
        return all_data_points
    
    async def process_and_validate_data(self, data_points: List[HealthDataPoint]) -> List[HealthDataPoint]:
        """Process and validate health data points"""
        validated_points = []
        
        for point in data_points:
            try:
                # Validate data point
                if self._validate_data_point(point):
                    # Normalize and clean data
                    processed_point = self._process_data_point(point)
                    validated_points.append(processed_point)
                else:
                    logger.warning(f"Invalid data point: {point}")
                    
            except Exception as e:
                logger.error(f"Error processing data point: {str(e)}")
                continue
        
        return validated_points
    
    def _validate_data_point(self, point: HealthDataPoint) -> bool:
        """Validate a health data point"""
        # Basic validation
        if not point.user_id or not point.data_type or point.timestamp is None:
            return False
        
        # Type-specific validation
        if point.data_type == DataType.HEART_RATE:
            if not isinstance(point.value, (int, float)) or point.value < 30 or point.value > 200:
                return False
        elif point.data_type == DataType.STEPS:
            if not isinstance(point.value, int) or point.value < 0:
                return False
        elif point.data_type == DataType.WEIGHT:
            if not isinstance(point.value, (int, float)) or point.value < 10 or point.value > 500:
                return False
        elif point.data_type == DataType.SLEEP:
            if not isinstance(point.value, (int, float)) or point.value < 0 or point.value > 1440:
                return False
        
        return True
    
    def _process_data_point(self, point: HealthDataPoint) -> HealthDataPoint:
        """Process and clean a data point"""
        # Apply data cleaning rules
        if point.data_type == DataType.HEART_RATE:
            # Remove outliers
            if point.value > 200 or point.value < 30:
                point.confidence = 0.0
        elif point.data_type == DataType.STEPS:
            # Cap unrealistic step counts
            if point.value > 50000:
                point.value = 50000
                point.confidence = 0.5
        
        # Add processing metadata
        if not point.metadata:
            point.metadata = {}
        point.metadata['processed_at'] = datetime.utcnow().isoformat()
        point.metadata['processing_version'] = '1.0'
        
        return point
    
    async def aggregate_health_metrics(self, user_id: int, data_points: List[HealthDataPoint], 
                                     aggregation_period: str = 'daily') -> HealthMetricsAggregation:
        """Aggregate health data points into metrics"""
        # Group data points by type and time period
        grouped_data = self._group_data_by_period(data_points, aggregation_period)
        
        # Calculate metrics for each group
        metrics = []
        for period, group_data in grouped_data.items():
            period_metrics = self._calculate_period_metrics(group_data)
            period_metrics['period'] = period
            period_metrics['user_id'] = user_id
            metrics.append(period_metrics)
        
        return metrics
    
    def _group_data_by_period(self, data_points: List[HealthDataPoint], period: str) -> Dict[str, List[HealthDataPoint]]:
        """Group data points by time period"""
        grouped = {}
        
        for point in data_points:
            if period == 'daily':
                key = point.timestamp.strftime('%Y-%m-%d')
            elif period == 'weekly':
                key = point.timestamp.strftime('%Y-W%U')
            elif period == 'monthly':
                key = point.timestamp.strftime('%Y-%m')
            else:
                key = point.timestamp.strftime('%Y-%m-%d')
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(point)
        
        return grouped
    
    def _calculate_period_metrics(self, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Calculate metrics for a group of data points"""
        metrics = {}
        
        # Group by data type
        by_type = {}
        for point in data_points:
            if point.data_type not in by_type:
                by_type[point.data_type] = []
            by_type[point.data_type].append(point)
        
        # Calculate metrics for each type
        for data_type, points in by_type.items():
            values = [p.value for p in points if isinstance(p.value, (int, float))]
            
            if values:
                if data_type == DataType.HEART_RATE:
                    metrics['avg_heart_rate'] = sum(values) / len(values)
                    metrics['min_heart_rate'] = min(values)
                    metrics['max_heart_rate'] = max(values)
                elif data_type == DataType.STEPS:
                    metrics['total_steps'] = sum(values)
                    metrics['avg_steps_per_day'] = sum(values) / len(values)
                elif data_type == DataType.WEIGHT:
                    metrics['avg_weight'] = sum(values) / len(values)
                    if len(values) > 1:
                        metrics['weight_change'] = values[-1] - values[0]
                elif data_type == DataType.SLEEP:
                    metrics['total_sleep_hours'] = sum(values) / 60  # Convert minutes to hours
                    metrics['avg_sleep_hours'] = sum(values) / len(values) / 60
        
        return metrics

# Factory for creating data providers
class DataProviderFactory:
    """Factory for creating data providers"""
    
    @staticmethod
    def create_provider(source_type: DataSourceType, config: DataSourceConfig) -> BaseDataProvider:
        """Create a data provider based on source type"""
        if source_type == DataSourceType.FITBIT:
            return FitbitDataProvider(config)
        elif source_type == DataSourceType.APPLE_HEALTH:
            return AppleHealthDataProvider(config)
        # Add more providers as needed
        else:
            raise ValueError(f"Unsupported data source type: {source_type}")

# Global data integration service instance
data_integration_service = DataIntegrationService() 