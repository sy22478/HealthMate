"""
ML Data Preparation Router
API endpoints for machine learning data preparation, feature engineering, and model training data
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.enhanced.ml_data_preparation import (
    get_ml_data_preparation_service, FeatureType, PreprocessingType, ModelType, DataVersion,
    FeatureDefinition, FeatureSet, ProcessedDataset, ModelVersion, ModelPerformance
)
from app.schemas.common_schemas import SuccessResponse
from app.utils.rate_limiting import rate_limiter
from app.utils.audit_logging import AuditLogger
from app.exceptions.health_exceptions import MLDataPreparationError

logger = logging.getLogger(__name__)

# Initialize router
ml_data_router = APIRouter(prefix="/api/v1/ml-data-preparation", tags=["ML Data Preparation"])

# Security
security = HTTPBearer()

@ml_data_router.post("/feature-sets/create", response_model=SuccessResponse)
async def create_feature_set(
    name: str = Body(..., description="Feature set name"),
    description: str = Body(..., description="Feature set description"),
    features: List[Dict[str, Any]] = Body(..., description="List of feature definitions"),
    target_variable: str = Body(..., description="Target variable name"),
    model_type: ModelType = Body(..., description="Type of ML model"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Create a new feature set for ML models.
    
    This endpoint creates a feature set with defined features for machine learning model training.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to create feature sets"
            )
        
        # Initialize ML data preparation service
        ml_service = get_ml_data_preparation_service(db)
        
        # Convert feature definitions
        feature_definitions = []
        for feature_data in features:
            feature_def = FeatureDefinition(
                name=feature_data['name'],
                feature_type=FeatureType(feature_data['feature_type']),
                source_table=feature_data['source_table'],
                source_column=feature_data['source_column'],
                description=feature_data['description'],
                preprocessing_steps=[PreprocessingType(step) for step in feature_data.get('preprocessing_steps', [])],
                validation_rules=feature_data.get('validation_rules', {}),
                is_required=feature_data.get('is_required', True),
                default_value=feature_data.get('default_value')
            )
            feature_definitions.append(feature_def)
        
        # Create feature set
        feature_set = ml_service.create_feature_set(
            name=name,
            description=description,
            features=feature_definitions,
            target_variable=target_variable,
            model_type=model_type
        )
        
        # Log creation
        AuditLogger.log_system_action(
            action="feature_set_created",
            user_id=current_user.id,
            details={
                "feature_set_id": feature_set.feature_set_id,
                "name": name,
                "model_type": model_type.value,
                "feature_count": len(feature_definitions)
            }
        )
        
        return SuccessResponse(
            message="Feature set created successfully",
            data={
                "feature_set": {
                    "feature_set_id": feature_set.feature_set_id,
                    "name": feature_set.name,
                    "description": feature_set.description,
                    "target_variable": feature_set.target_variable,
                    "model_type": feature_set.model_type.value,
                    "feature_count": len(feature_set.features),
                    "version": feature_set.version,
                    "created_at": feature_set.created_at.isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except MLDataPreparationError as e:
        logger.error(f"ML data preparation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating feature set: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create feature set: {str(e)}")

@ml_data_router.post("/datasets/prepare", response_model=SuccessResponse)
async def prepare_ml_dataset(
    feature_set_id: str = Body(..., description="Feature set ID"),
    user_ids: List[int] = Body(..., description="List of user IDs"),
    target_variable: str = Body(..., description="Target variable name"),
    test_size: float = Body(0.2, description="Test set size (0.0 to 1.0)"),
    random_state: int = Body(42, description="Random state for reproducibility"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Prepare a machine learning dataset.
    
    This endpoint prepares a complete ML dataset with features extracted from user data.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to prepare ML datasets"
            )
        
        # Initialize ML data preparation service
        ml_service = get_ml_data_preparation_service(db)
        
        # Create a placeholder feature set (in real implementation, this would be loaded from database)
        feature_set = FeatureSet(
            feature_set_id=feature_set_id,
            name="Health Prediction Features",
            description="Features for health outcome prediction",
            features=[],
            target_variable=target_variable,
            model_type=ModelType.REGRESSION
        )
        
        # Prepare dataset
        dataset = await ml_service.prepare_ml_dataset(
            user_ids=user_ids,
            feature_set=feature_set,
            target_variable=target_variable,
            test_size=test_size,
            random_state=random_state
        )
        
        # Log dataset preparation
        AuditLogger.log_system_action(
            action="ml_dataset_prepared",
            user_id=current_user.id,
            details={
                "dataset_id": dataset.dataset_id,
                "feature_set_id": feature_set_id,
                "user_count": len(user_ids),
                "feature_count": len(dataset.features),
                "test_size": test_size
            }
        )
        
        return SuccessResponse(
            message="ML dataset prepared successfully",
            data={
                "dataset": {
                    "dataset_id": dataset.dataset_id,
                    "feature_set_id": dataset.feature_set_id,
                    "data_hash": dataset.data_hash,
                    "features": dataset.features,
                    "target_variable": dataset.target_variable,
                    "feature_count": len(dataset.feature_names),
                    "train_samples": len(dataset.X_train),
                    "test_samples": len(dataset.X_test),
                    "metadata": dataset.metadata,
                    "created_at": dataset.created_at.isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except MLDataPreparationError as e:
        logger.error(f"ML data preparation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error preparing ML dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to prepare ML dataset: {str(e)}")

@ml_data_router.get("/features/extract", response_model=SuccessResponse)
async def extract_features(
    user_id: int = Query(..., description="User ID"),
    start_date: datetime = Query(..., description="Start date for feature extraction"),
    end_date: datetime = Query(..., description="End date for feature extraction"),
    feature_types: List[str] = Query(["health", "engagement", "temporal"], description="Types of features to extract"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Extract features for a specific user.
    
    This endpoint extracts various types of features for machine learning models.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges or is requesting their own data
        if current_user.role != "admin" and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only extract features for your own data or with admin privileges"
            )
        
        # Initialize ML data preparation service
        ml_service = get_ml_data_preparation_service(db)
        
        extracted_features = {}
        
        # Extract health features
        if "health" in feature_types:
            health_features = await ml_service.feature_engineering.extract_health_features(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            extracted_features["health"] = health_features
        
        # Extract engagement features
        if "engagement" in feature_types:
            engagement_features = await ml_service.feature_engineering.extract_engagement_features(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            extracted_features["engagement"] = engagement_features
        
        # Extract temporal features
        if "temporal" in feature_types:
            temporal_features = await ml_service.feature_engineering.extract_temporal_features(
                timestamp=end_date
            )
            extracted_features["temporal"] = temporal_features
        
        # Log feature extraction
        AuditLogger.log_data_access(
            user_id=current_user.id,
            data_type="ml_features",
            access_type="read",
            details={
                "target_user_id": user_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "feature_types": feature_types
            }
        )
        
        return SuccessResponse(
            message="Features extracted successfully",
            data={
                "user_id": user_id,
                "feature_types": feature_types,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "features": extracted_features
            }
        )
        
    except HTTPException:
        raise
    except MLDataPreparationError as e:
        logger.error(f"ML data preparation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error extracting features: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract features: {str(e)}")

@ml_data_router.post("/data/preprocess", response_model=SuccessResponse)
async def preprocess_data(
    features: Dict[str, Any] = Body(..., description="Features to preprocess"),
    preprocessing_config: Dict[str, Any] = Body(..., description="Preprocessing configuration"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Preprocess data for ML models.
    
    This endpoint preprocesses features according to the specified configuration.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to preprocess ML data"
            )
        
        # Initialize ML data preparation service
        ml_service = get_ml_data_preparation_service(db)
        
        # Preprocess features
        processed_features = ml_service.preprocessor.preprocess_features(
            features=features,
            preprocessing_config=preprocessing_config
        )
        
        # Log preprocessing
        AuditLogger.log_system_action(
            action="ml_data_preprocessed",
            user_id=current_user.id,
            details={
                "input_features": len(features),
                "output_features": len(processed_features),
                "preprocessing_config": preprocessing_config
            }
        )
        
        return SuccessResponse(
            message="Data preprocessed successfully",
            data={
                "input_features": len(features),
                "output_features": len(processed_features),
                "processed_features": processed_features,
                "preprocessing_config": preprocessing_config
            }
        )
        
    except HTTPException:
        raise
    except MLDataPreparationError as e:
        logger.error(f"ML data preparation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error preprocessing data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preprocess data: {str(e)}")

@ml_data_router.get("/datasets/versions", response_model=SuccessResponse)
async def list_dataset_versions(
    dataset_id: str = Query(..., description="Dataset ID"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    List versions of a dataset.
    
    This endpoint lists all available versions of a specific dataset.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to list dataset versions"
            )
        
        # Initialize ML data preparation service
        ml_service = get_ml_data_preparation_service(db)
        
        # List versions
        versions = ml_service.versioning.list_dataset_versions(dataset_id)
        
        # Log access
        AuditLogger.log_data_access(
            user_id=current_user.id,
            data_type="dataset_versions",
            access_type="read",
            details={
                "dataset_id": dataset_id,
                "version_count": len(versions)
            }
        )
        
        return SuccessResponse(
            message="Dataset versions retrieved successfully",
            data={
                "dataset_id": dataset_id,
                "versions": versions,
                "version_count": len(versions)
            }
        )
        
    except HTTPException:
        raise
    except MLDataPreparationError as e:
        logger.error(f"ML data preparation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing dataset versions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list dataset versions: {str(e)}")

@ml_data_router.get("/datasets/load-version", response_model=SuccessResponse)
async def load_dataset_version(
    dataset_id: str = Query(..., description="Dataset ID"),
    version: str = Query(..., description="Dataset version"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Load a specific version of a dataset.
    
    This endpoint loads a specific version of a dataset for analysis or model training.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to load dataset versions"
            )
        
        # Initialize ML data preparation service
        ml_service = get_ml_data_preparation_service(db)
        
        # Load dataset version
        dataset = ml_service.versioning.load_dataset_version(dataset_id, version)
        
        # Log access
        AuditLogger.log_data_access(
            user_id=current_user.id,
            data_type="dataset_version",
            access_type="read",
            details={
                "dataset_id": dataset_id,
                "version": version,
                "feature_count": len(dataset.features)
            }
        )
        
        return SuccessResponse(
            message="Dataset version loaded successfully",
            data={
                "dataset": {
                    "dataset_id": dataset.dataset_id,
                    "version": version,
                    "feature_set_id": dataset.feature_set_id,
                    "data_hash": dataset.data_hash,
                    "features": dataset.features,
                    "target_variable": dataset.target_variable,
                    "feature_count": len(dataset.feature_names),
                    "train_samples": len(dataset.X_train),
                    "test_samples": len(dataset.X_test),
                    "metadata": dataset.metadata,
                    "created_at": dataset.created_at.isoformat()
                }
            }
        )
        
    except HTTPException:
        raise
    except MLDataPreparationError as e:
        logger.error(f"ML data preparation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error loading dataset version: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load dataset version: {str(e)}")

@ml_data_router.get("/models/performance", response_model=SuccessResponse)
async def get_model_performance_history(
    model_id: str = Query(..., description="Model ID"),
    metric_name: Optional[str] = Query(None, description="Specific metric name"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Get model performance history.
    
    This endpoint retrieves performance history for a specific model.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to access model performance data"
            )
        
        # Initialize ML data preparation service
        ml_service = get_ml_data_preparation_service(db)
        
        # Get performance history
        performance_history = await ml_service.performance_tracker.get_model_performance_history(
            model_id=model_id,
            metric_name=metric_name
        )
        
        # Log access
        AuditLogger.log_data_access(
            user_id=current_user.id,
            data_type="model_performance",
            access_type="read",
            details={
                "model_id": model_id,
                "metric_name": metric_name,
                "performance_count": len(performance_history)
            }
        )
        
        return SuccessResponse(
            message="Model performance history retrieved successfully",
            data={
                "model_id": model_id,
                "metric_name": metric_name,
                "performance_history": [
                    {
                        "version": perf.version,
                        "metric_name": perf.metric_name,
                        "metric_value": perf.metric_value,
                        "evaluation_date": perf.evaluation_date.isoformat(),
                        "dataset_split": perf.dataset_split,
                        "environment": perf.environment
                    }
                    for perf in performance_history
                ],
                "performance_count": len(performance_history)
            }
        )
        
    except HTTPException:
        raise
    except MLDataPreparationError as e:
        logger.error(f"ML data preparation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting model performance history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model performance history: {str(e)}")

@ml_data_router.get("/dashboard/summary", response_model=SuccessResponse)
async def get_ml_data_preparation_dashboard_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> SuccessResponse:
    """
    Get ML data preparation dashboard summary.
    
    This endpoint provides a summary of ML data preparation activities and metrics.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to access ML data preparation dashboard"
            )
        
        # In a real implementation, this would aggregate data from various ML tables
        # For now, return a placeholder summary
        dashboard_summary = {
            "feature_sets": {
                "total_feature_sets": 5,
                "active_feature_sets": 3,
                "features_extracted_today": 1250
            },
            "datasets": {
                "total_datasets": 12,
                "datasets_prepared_today": 3,
                "avg_dataset_size": 5000,
                "total_versions": 45
            },
            "models": {
                "total_models": 8,
                "active_models": 6,
                "avg_model_accuracy": 0.87,
                "models_trained_today": 2
            },
            "performance": {
                "feature_extraction_time_avg_ms": 250,
                "dataset_preparation_time_avg_ms": 1200,
                "preprocessing_time_avg_ms": 180,
                "success_rate": 0.95
            }
        }
        
        # Log access
        AuditLogger.log_data_access(
            user_id=current_user.id,
            data_type="ml_dashboard",
            access_type="read",
            details={}
        )
        
        return SuccessResponse(
            message="ML data preparation dashboard summary retrieved successfully",
            data=dashboard_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ML data preparation dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ML data preparation dashboard summary: {str(e)}") 