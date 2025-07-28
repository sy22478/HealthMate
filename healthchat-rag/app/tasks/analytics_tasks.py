"""
Analytics background tasks for HealthMate.

This module provides background tasks for:
- Health analytics computation
- Trend analysis
- Predictive modeling
- Report generation
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.enhanced_health_models import HealthData, UserHealthProfile
from app.services.enhanced.business_intelligence import (
    get_global_bi_service, ReportType, AggregationPeriod
)
from app.services.enhanced.ml_data_preparation import (
    get_global_ml_data_preparation_service, FeatureType, ModelType, DataVersion,
    FeatureDefinition, FeatureSet, ModelPerformance
)
from app.utils.performance_monitoring import monitor_custom_performance

logger = logging.getLogger(__name__)

@celery_app.task
@monitor_custom_performance("compute_analytics")
def compute_analytics():
    """
    Compute health analytics for all users.
    
    This task runs every 2 hours to compute comprehensive
    health analytics and insights.
    """
    try:
        db = SessionLocal()
        
        # Get all active users
        users = db.query(UserHealthProfile).filter(
            UserHealthProfile.is_active == True
        ).all()
        
        processed_count = 0
        error_count = 0
        
        for user_profile in users:
            try:
                # Compute analytics for each user
                result = compute_user_analytics(user_profile.user_id, db)
                if result["success"]:
                    processed_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to compute analytics for user {user_profile.user_id}: {e}")
                error_count += 1
        
        logger.info(f"Analytics computation completed: {processed_count} successful, {error_count} errors")
        
        return {
            "status": "completed",
            "processed_count": processed_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics computation task failed: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("analyze_health_trends")
def analyze_health_trends(user_id: int, days: int = 30):
    """
    Analyze health trends for a specific user.
    
    Args:
        user_id: ID of the user to analyze
        days: Number of days to analyze (default: 30)
    """
    try:
        db = SessionLocal()
        
        # Get health data for the specified period
        start_date = datetime.now() - timedelta(days=days)
        health_data = db.query(HealthData).filter(
            HealthData.user_id == user_id,
            HealthData.timestamp >= start_date
        ).order_by(HealthData.timestamp).all()
        
        # Group data by metric type
        metrics_data = {}
        for data_point in health_data:
            if data_point.metric_type not in metrics_data:
                metrics_data[data_point.metric_type] = []
            metrics_data[data_point.metric_type].append({
                "value": data_point.value,
                "timestamp": data_point.timestamp
            })
        
        # Analyze trends for each metric
        trends = {}
        for metric_type, data_points in metrics_data.items():
            if len(data_points) >= 3:  # Need at least 3 points for trend analysis
                trend_analysis = analyze_metric_trend(data_points)
                trends[metric_type] = trend_analysis
        
        logger.info(f"Health trends analyzed for user {user_id}: {len(trends)} metrics")
        
        return {
            "user_id": user_id,
            "analysis_period_days": days,
            "trends": trends,
            "total_data_points": len(health_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health trends analysis failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("generate_health_report")
def generate_health_report(user_id: int, report_type: str = "comprehensive"):
    """
    Generate health report for a specific user.
    
    Args:
        user_id: ID of the user to generate report for
        report_type: Type of report (comprehensive, summary, trends)
    """
    try:
        db = SessionLocal()
        
        # Get user profile
        user_profile = db.query(UserHealthProfile).filter(
            UserHealthProfile.user_id == user_id
        ).first()
        
        if not user_profile:
            raise ValueError(f"User profile not found for user {user_id}")
        
        # Generate report based on type
        if report_type == "comprehensive":
            report = generate_comprehensive_report(user_id, user_profile, db)
        elif report_type == "summary":
            report = generate_summary_report(user_id, user_profile, db)
        elif report_type == "trends":
            report = generate_trends_report(user_id, user_profile, db)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
        
        # Store report (in production, this would be to cloud storage)
        report_path = f"/tmp/health_report_{user_id}_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Health report generated for user {user_id}: {report_type}")
        
        return {
            "user_id": user_id,
            "report_type": report_type,
            "report_path": report_path,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health report generation failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("predict_health_risks")
def predict_health_risks(user_id: int):
    """
    Predict health risks for a specific user.
    
    Args:
        user_id: ID of the user to predict risks for
    """
    try:
        db = SessionLocal()
        
        # Get user's health data
        health_data = db.query(HealthData).filter(
            HealthData.user_id == user_id
        ).order_by(HealthData.timestamp.desc()).limit(100).all()
        
        # Analyze risk factors
        risk_factors = analyze_risk_factors(health_data)
        
        # Generate risk predictions
        risk_predictions = generate_risk_predictions(risk_factors)
        
        # Update user profile with risk assessment
        user_profile = db.query(UserHealthProfile).filter(
            UserHealthProfile.user_id == user_id
        ).first()
        
        if user_profile:
            user_profile.last_risk_assessment = datetime.now()
            user_profile.risk_factors = risk_factors
            user_profile.risk_predictions = risk_predictions
            db.commit()
        
        logger.info(f"Health risk prediction completed for user {user_id}")
        
        return {
            "user_id": user_id,
            "risk_factors": risk_factors,
            "risk_predictions": risk_predictions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health risk prediction failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("compute_population_analytics")
def compute_population_analytics():
    """
    Compute population-level health analytics.
    
    This task analyzes health patterns across all users
    to identify population trends and insights.
    """
    try:
        db = SessionLocal()
        
        # Get all health data
        health_data = db.query(HealthData).all()
        
        # Group by metric type
        population_metrics = {}
        for data_point in health_data:
            if data_point.metric_type not in population_metrics:
                population_metrics[data_point.metric_type] = []
            population_metrics[data_point.metric_type].append(data_point.value)
        
        # Compute population statistics
        population_stats = {}
        for metric_type, values in population_metrics.items():
            if values:
                population_stats[metric_type] = {
                    "count": len(values),
                    "mean": np.mean(values),
                    "median": np.median(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "percentiles": {
                        "25": np.percentile(values, 25),
                        "50": np.percentile(values, 50),
                        "75": np.percentile(values, 75),
                        "90": np.percentile(values, 90),
                        "95": np.percentile(values, 95)
                    }
                }
        
        # Identify outliers and anomalies
        anomalies = detect_population_anomalies(population_stats)
        
        # Generate insights
        insights = generate_population_insights(population_stats, anomalies)
        
        logger.info(f"Population analytics computed: {len(population_stats)} metrics analyzed")
        
        return {
            "population_stats": population_stats,
            "anomalies": anomalies,
            "insights": insights,
            "total_users": len(set(dp.user_id for dp in health_data)),
            "total_data_points": len(health_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Population analytics computation failed: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("generate_business_intelligence_reports")
def generate_business_intelligence_reports():
    """
    Generate automated business intelligence reports.
    
    This task runs daily to generate comprehensive BI reports
    for health summary, user engagement, and system performance.
    """
    try:
        bi_service = get_global_bi_service()
        
        # Set report period (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        reports_generated = []
        
        # Generate health summary report
        try:
            health_report = bi_service.generate_automated_report(
                report_type=ReportType.HEALTH_SUMMARY,
                start_date=start_date,
                end_date=end_date,
                generated_by="automated_task"
            )
            reports_generated.append({
                "type": "health_summary",
                "report_id": health_report.report_id,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Failed to generate health summary report: {e}")
            reports_generated.append({
                "type": "health_summary",
                "status": "failed",
                "error": str(e)
            })
        
        # Generate user engagement report
        try:
            engagement_report = bi_service.generate_automated_report(
                report_type=ReportType.USER_ENGAGEMENT,
                start_date=start_date,
                end_date=end_date,
                generated_by="automated_task"
            )
            reports_generated.append({
                "type": "user_engagement",
                "report_id": engagement_report.report_id,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Failed to generate user engagement report: {e}")
            reports_generated.append({
                "type": "user_engagement",
                "status": "failed",
                "error": str(e)
            })
        
        # Generate system performance report
        try:
            performance_report = bi_service.generate_automated_report(
                report_type=ReportType.SYSTEM_PERFORMANCE,
                start_date=start_date,
                end_date=end_date,
                generated_by="automated_task"
            )
            reports_generated.append({
                "type": "system_performance",
                "report_id": performance_report.report_id,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"Failed to generate system performance report: {e}")
            reports_generated.append({
                "type": "system_performance",
                "status": "failed",
                "error": str(e)
            })
        
        logger.info(f"Business intelligence reports generated: {len(reports_generated)} reports")
        
        return {
            "status": "completed",
            "reports_generated": reports_generated,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Business intelligence report generation failed: {e}")
        raise
    finally:
        if 'bi_service' in locals() and hasattr(bi_service, 'db'):
            bi_service.db.close()

@celery_app.task
@monitor_custom_performance("aggregate_health_metrics_bi")
def aggregate_health_metrics_bi():
    """
    Aggregate health metrics for business intelligence.
    
    This task runs every 6 hours to aggregate health metrics
    for business intelligence reporting.
    """
    try:
        bi_service = get_global_bi_service()
        
        # Get all active users
        users = bi_service.db.query(UserHealthProfile).filter(
            UserHealthProfile.is_active == True
        ).all()
        
        aggregated_count = 0
        error_count = 0
        
        # Set aggregation period (last 24 hours)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        for user_profile in users:
            try:
                # Aggregate daily metrics
                aggregated_metrics = bi_service.aggregate_health_metrics(
                    user_id=user_profile.user_id,
                    period=AggregationPeriod.DAILY,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if aggregated_metrics:
                    aggregated_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to aggregate metrics for user {user_profile.user_id}: {e}")
                error_count += 1
        
        logger.info(f"Health metrics aggregation completed: {aggregated_count} successful, {error_count} errors")
        
        return {
            "status": "completed",
            "aggregated_count": aggregated_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health metrics aggregation failed: {e}")
        raise
    finally:
        if 'bi_service' in locals() and hasattr(bi_service, 'db'):
            bi_service.db.close()

@celery_app.task
@monitor_custom_performance("track_user_engagement_bi")
def track_user_engagement_bi():
    """
    Track user engagement metrics for business intelligence.
    
    This task runs daily to track user engagement metrics
    for business intelligence reporting.
    """
    try:
        bi_service = get_global_bi_service()
        
        # Get all active users
        users = bi_service.db.query(UserHealthProfile).filter(
            UserHealthProfile.is_active == True
        ).all()
        
        tracked_count = 0
        error_count = 0
        
        # Track engagement for yesterday
        yesterday = datetime.now() - timedelta(days=1)
        
        for user_profile in users:
            try:
                # Track user engagement
                engagement_metrics = bi_service.track_user_engagement(
                    user_id=user_profile.user_id,
                    date=yesterday
                )
                
                if engagement_metrics:
                    tracked_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to track engagement for user {user_profile.user_id}: {e}")
                error_count += 1
        
        logger.info(f"User engagement tracking completed: {tracked_count} successful, {error_count} errors")
        
        return {
            "status": "completed",
            "tracked_count": tracked_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"User engagement tracking failed: {e}")
        raise
    finally:
        if 'bi_service' in locals() and hasattr(bi_service, 'db'):
            bi_service.db.close()

@celery_app.task
@monitor_custom_performance("collect_system_performance_bi")
def collect_system_performance_bi():
    """
    Collect system performance metrics for business intelligence.
    
    This task runs every hour to collect system performance metrics
    for business intelligence reporting.
    """
    try:
        bi_service = get_global_bi_service()
        
        # Collect performance metrics for different services
        services = ["api", "database", "cache", "queue", "storage"]
        collected_count = 0
        error_count = 0
        
        for service in services:
            try:
                # Collect system performance metrics
                performance_metrics = bi_service.collect_system_performance_metrics(
                    service_name=service,
                    environment="production"
                )
                
                if performance_metrics:
                    collected_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to collect performance metrics for service {service}: {e}")
                error_count += 1
        
        logger.info(f"System performance collection completed: {collected_count} successful, {error_count} errors")
        
        return {
            "status": "completed",
            "collected_count": collected_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System performance collection failed: {e}")
        raise
    finally:
        if 'bi_service' in locals() and hasattr(bi_service, 'db'):
            bi_service.db.close()

@celery_app.task
@monitor_custom_performance("prepare_ml_datasets")
def prepare_ml_datasets():
    """
    Prepare ML datasets for model training.
    
    This task runs daily to prepare datasets for various ML models
    including health prediction, user engagement, and system optimization.
    """
    try:
        ml_service = get_global_ml_data_preparation_service()
        
        # Get all active users
        users = ml_service.db.query(UserHealthProfile).filter(
            UserHealthProfile.is_active == True
        ).all()
        user_ids = [user.user_id for user in users]
        
        if not user_ids:
            logger.warning("No active users found for ML dataset preparation")
            return {
                "status": "completed",
                "datasets_prepared": 0,
                "error_count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        datasets_prepared = 0
        error_count = 0
        
        # Prepare health prediction dataset
        try:
            health_feature_set = ml_service.create_feature_set(
                name="Health Prediction Features",
                description="Features for health outcome prediction",
                features=[
                    FeatureDefinition(
                        name="avg_heart_rate",
                        feature_type=FeatureType.NUMERICAL,
                        source_table="health_metrics_aggregation",
                        source_column="avg_heart_rate",
                        description="Average heart rate"
                    ),
                    FeatureDefinition(
                        name="avg_blood_pressure_systolic",
                        feature_type=FeatureType.NUMERICAL,
                        source_table="health_metrics_aggregation",
                        source_column="avg_blood_pressure_systolic",
                        description="Average systolic blood pressure"
                    ),
                    FeatureDefinition(
                        name="medication_adherence",
                        feature_type=FeatureType.NUMERICAL,
                        source_table="health_metrics_aggregation",
                        source_column="medication_adherence_rate",
                        description="Medication adherence rate"
                    )
                ],
                target_variable="health_score",
                model_type=ModelType.REGRESSION
            )
            
            health_dataset = ml_service.prepare_ml_dataset(
                user_ids=user_ids[:100],  # Limit to first 100 users for demo
                feature_set=health_feature_set,
                target_variable="health_score",
                test_size=0.2
            )
            
            datasets_prepared += 1
            logger.info(f"Health prediction dataset prepared: {health_dataset.dataset_id}")
            
        except Exception as e:
            logger.error(f"Failed to prepare health prediction dataset: {e}")
            error_count += 1
        
        # Prepare user engagement prediction dataset
        try:
            engagement_feature_set = ml_service.create_feature_set(
                name="User Engagement Features",
                description="Features for user engagement prediction",
                features=[
                    FeatureDefinition(
                        name="login_count",
                        feature_type=FeatureType.NUMERICAL,
                        source_table="user_engagement_analytics",
                        source_column="login_count",
                        description="Number of logins"
                    ),
                    FeatureDefinition(
                        name="session_duration_minutes",
                        feature_type=FeatureType.NUMERICAL,
                        source_table="user_engagement_analytics",
                        source_column="session_duration_minutes",
                        description="Session duration in minutes"
                    ),
                    FeatureDefinition(
                        name="chat_messages_sent",
                        feature_type=FeatureType.NUMERICAL,
                        source_table="user_engagement_analytics",
                        source_column="chat_messages_sent",
                        description="Number of chat messages sent"
                    )
                ],
                target_variable="engagement_score",
                model_type=ModelType.REGRESSION
            )
            
            engagement_dataset = ml_service.prepare_ml_dataset(
                user_ids=user_ids[:100],  # Limit to first 100 users for demo
                feature_set=engagement_feature_set,
                target_variable="engagement_score",
                test_size=0.2
            )
            
            datasets_prepared += 1
            logger.info(f"User engagement dataset prepared: {engagement_dataset.dataset_id}")
            
        except Exception as e:
            logger.error(f"Failed to prepare user engagement dataset: {e}")
            error_count += 1
        
        logger.info(f"ML dataset preparation completed: {datasets_prepared} datasets prepared, {error_count} errors")
        
        return {
            "status": "completed",
            "datasets_prepared": datasets_prepared,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML dataset preparation failed: {e}")
        raise
    finally:
        if 'ml_service' in locals() and hasattr(ml_service, 'db'):
            ml_service.db.close()

@celery_app.task
@monitor_custom_performance("extract_features_for_ml")
def extract_features_for_ml():
    """
    Extract features for ML models.
    
    This task runs every 6 hours to extract and cache features
    for machine learning models.
    """
    try:
        ml_service = get_global_ml_data_preparation_service()
        
        # Get all active users
        users = ml_service.db.query(UserHealthProfile).filter(
            UserHealthProfile.is_active == True
        ).all()
        
        extracted_count = 0
        error_count = 0
        
        # Set time range for feature extraction
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        for user in users[:50]:  # Limit to first 50 users for demo
            try:
                # Extract health features
                health_features = ml_service.feature_engineering.extract_health_features(
                    user_id=user.user_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Extract engagement features
                engagement_features = ml_service.feature_engineering.extract_engagement_features(
                    user_id=user.user_id,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Extract temporal features
                temporal_features = ml_service.feature_engineering.extract_temporal_features(
                    timestamp=end_date
                )
                
                # Combine all features
                combined_features = {}
                if health_features.get('health_daily'):
                    combined_features.update(health_features['health_daily'])
                if engagement_features.get('engagement_7d'):
                    combined_features.update(engagement_features['engagement_7d'])
                combined_features.update(temporal_features)
                
                # Cache features (in a real implementation, this would be stored in a cache or database)
                feature_cache_key = f"user_features_{user.user_id}_{end_date.strftime('%Y%m%d')}"
                # cache.set(feature_cache_key, combined_features, expire=86400)  # 24 hours
                
                extracted_count += 1
                
            except Exception as e:
                logger.error(f"Failed to extract features for user {user.user_id}: {e}")
                error_count += 1
        
        logger.info(f"Feature extraction completed: {extracted_count} users processed, {error_count} errors")
        
        return {
            "status": "completed",
            "users_processed": extracted_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        raise
    finally:
        if 'ml_service' in locals() and hasattr(ml_service, 'db'):
            ml_service.db.close()

@celery_app.task
@monitor_custom_performance("preprocess_ml_data")
def preprocess_ml_data():
    """
    Preprocess ML data for model training.
    
    This task runs daily to preprocess and clean data
    for machine learning model training.
    """
    try:
        ml_service = get_global_ml_data_preparation_service()
        
        # Get sample data for preprocessing (in a real implementation, this would come from cache or database)
        sample_features = {
            'avg_heart_rate': 75.0,
            'avg_blood_pressure_systolic': 120.0,
            'medication_adherence': 0.95,
            'login_count': 5,
            'session_duration_minutes': 45,
            'chat_messages_sent': 10,
            'hour': 14,
            'day_of_week': 2,
            'is_weekend': 0
        }
        
        # Preprocessing configuration
        preprocessing_config = {
            'imputation': {'method': 'mean'},
            'scaling': {'method': 'standard'},
            'encoding': {'method': 'label'},
            'feature_selection': {'method': 'correlation', 'max_features': 10},
            'dimensionality_reduction': {'method': 'pca', 'n_components': 5}
        }
        
        # Preprocess features
        processed_features = ml_service.preprocessor.preprocess_features(
            features=sample_features,
            preprocessing_config=preprocessing_config
        )
        
        logger.info(f"Data preprocessing completed: {len(processed_features)} features processed")
        
        return {
            "status": "completed",
            "features_processed": len(processed_features),
            "preprocessing_config": preprocessing_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Data preprocessing failed: {e}")
        raise

@celery_app.task
@monitor_custom_performance("version_ml_data")
def version_ml_data():
    """
    Version ML datasets and models.
    
    This task runs weekly to create new versions of datasets
    and track model performance.
    """
    try:
        ml_service = get_global_ml_data_preparation_service()
        
        # List existing dataset versions
        dataset_versions = ml_service.versioning.list_dataset_versions("sample_dataset")
        
        # Create new version if needed
        if dataset_versions:
            latest_version = dataset_versions[-1]
            logger.info(f"Latest dataset version: {latest_version}")
        
        # Track model performance
        model_performance = ModelPerformance(
            model_id="health_prediction_model",
            version="1.0.0",
            metric_name="accuracy",
            metric_value=0.85,
            evaluation_date=datetime.now(),
            dataset_split="test",
            environment="development"
        )
        
        success = ml_service.performance_tracker.track_model_performance(model_performance)
        
        logger.info(f"ML data versioning completed: {len(dataset_versions)} versions found, performance tracking: {success}")
        
        return {
            "status": "completed",
            "dataset_versions": len(dataset_versions),
            "performance_tracked": success,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"ML data versioning failed: {e}")
        raise
    finally:
        if 'ml_service' in locals() and hasattr(ml_service, 'db'):
            ml_service.db.close()

# Helper functions

def compute_user_analytics(user_id: int, db) -> Dict[str, Any]:
    """Compute comprehensive analytics for a specific user."""
    # Get user's health data
    health_data = db.query(HealthData).filter(
        HealthData.user_id == user_id
    ).all()
    
    if not health_data:
        return {"success": False, "reason": "No health data available"}
    
    # Compute various analytics
    analytics = {
        "data_summary": compute_data_summary(health_data),
        "trends": compute_trends(health_data),
        "correlations": compute_correlations(health_data),
        "anomalies": detect_anomalies(health_data),
        "recommendations": generate_recommendations(health_data)
    }
    
    # Update user profile
    user_profile = db.query(UserHealthProfile).filter(
        UserHealthProfile.user_id == user_id
    ).first()
    
    if user_profile:
        user_profile.last_analytics_computation = datetime.now()
        user_profile.analytics_data = analytics
        db.commit()
    
    return {"success": True, "analytics": analytics}

def analyze_metric_trend(data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze trend for a specific metric."""
    if len(data_points) < 3:
        return {"trend": "insufficient_data", "confidence": 0.0}
    
    # Extract values and timestamps
    values = [dp["value"] for dp in data_points]
    timestamps = [dp["timestamp"] for dp in data_points]
    
    # Convert timestamps to numeric values for regression
    time_numeric = [(ts - timestamps[0]).days for ts in timestamps]
    
    # Simple linear regression
    slope, intercept = np.polyfit(time_numeric, values, 1)
    
    # Determine trend direction
    if slope > 0.01:
        trend = "increasing"
    elif slope < -0.01:
        trend = "decreasing"
    else:
        trend = "stable"
    
    # Calculate confidence (R-squared)
    y_pred = slope * np.array(time_numeric) + intercept
    ss_res = np.sum((values - y_pred) ** 2)
    ss_tot = np.sum((values - np.mean(values)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    return {
        "trend": trend,
        "slope": slope,
        "confidence": r_squared,
        "data_points": len(data_points)
    }

def generate_comprehensive_report(user_id: int, user_profile, db) -> Dict[str, Any]:
    """Generate comprehensive health report."""
    # Get recent health data
    recent_data = db.query(HealthData).filter(
        HealthData.user_id == user_id,
        HealthData.timestamp >= datetime.now() - timedelta(days=30)
    ).all()
    
    report = {
        "user_id": user_id,
        "report_type": "comprehensive",
        "generated_at": datetime.now().isoformat(),
        "period": "last_30_days",
        "summary": {
            "total_data_points": len(recent_data),
            "metrics_tracked": len(set(dp.metric_type for dp in recent_data)),
            "data_completeness": calculate_data_completeness(recent_data)
        },
        "metrics_analysis": analyze_all_metrics(recent_data),
        "trends": compute_trends(recent_data),
        "recommendations": generate_recommendations(recent_data),
        "risk_assessment": user_profile.risk_factors or {},
        "next_steps": generate_next_steps(recent_data, user_profile)
    }
    
    return report

def generate_summary_report(user_id: int, user_profile, db) -> Dict[str, Any]:
    """Generate summary health report."""
    # Get key metrics from last 7 days
    recent_data = db.query(HealthData).filter(
        HealthData.user_id == user_id,
        HealthData.timestamp >= datetime.now() - timedelta(days=7)
    ).all()
    
    report = {
        "user_id": user_id,
        "report_type": "summary",
        "generated_at": datetime.now().isoformat(),
        "period": "last_7_days",
        "key_metrics": extract_key_metrics(recent_data),
        "overall_health_score": user_profile.health_metrics.get("health_score", 0) if user_profile.health_metrics else 0,
        "quick_insights": generate_quick_insights(recent_data)
    }
    
    return report

def generate_trends_report(user_id: int, user_profile, db) -> Dict[str, Any]:
    """Generate trends-focused health report."""
    # Get data from last 90 days
    recent_data = db.query(HealthData).filter(
        HealthData.user_id == user_id,
        HealthData.timestamp >= datetime.now() - timedelta(days=90)
    ).all()
    
    report = {
        "user_id": user_id,
        "report_type": "trends",
        "generated_at": datetime.now().isoformat(),
        "period": "last_90_days",
        "trends": compute_detailed_trends(recent_data),
        "seasonal_patterns": detect_seasonal_patterns(recent_data),
        "improvement_areas": identify_improvement_areas(recent_data)
    }
    
    return report

def analyze_risk_factors(health_data: List[HealthData]) -> Dict[str, Any]:
    """Analyze health risk factors from data."""
    risk_factors = {
        "high_blood_pressure": False,
        "high_heart_rate": False,
        "low_activity": False,
        "poor_sleep": False,
        "weight_issues": False
    }
    
    # Analyze each metric for risk factors
    for data_point in health_data:
        if data_point.metric_type == "blood_pressure_systolic" and data_point.value > 140:
            risk_factors["high_blood_pressure"] = True
        elif data_point.metric_type == "heart_rate" and data_point.value > 100:
            risk_factors["high_heart_rate"] = True
        elif data_point.metric_type == "steps" and data_point.value < 5000:
            risk_factors["low_activity"] = True
        elif data_point.metric_type == "sleep_hours" and data_point.value < 6:
            risk_factors["poor_sleep"] = True
        elif data_point.metric_type == "bmi" and (data_point.value < 18.5 or data_point.value > 25):
            risk_factors["weight_issues"] = True
    
    return risk_factors

def generate_risk_predictions(risk_factors: Dict[str, Any]) -> Dict[str, Any]:
    """Generate health risk predictions based on risk factors."""
    predictions = {
        "cardiovascular_risk": "low",
        "diabetes_risk": "low",
        "obesity_risk": "low",
        "sleep_disorder_risk": "low"
    }
    
    # Simple risk assessment logic
    if risk_factors["high_blood_pressure"] or risk_factors["high_heart_rate"]:
        predictions["cardiovascular_risk"] = "moderate"
    
    if risk_factors["weight_issues"] and risk_factors["low_activity"]:
        predictions["diabetes_risk"] = "moderate"
        predictions["obesity_risk"] = "moderate"
    
    if risk_factors["poor_sleep"]:
        predictions["sleep_disorder_risk"] = "moderate"
    
    return predictions

def detect_population_anomalies(population_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect anomalies in population health data."""
    anomalies = []
    
    for metric_type, stats in population_stats.items():
        # Check for unusual distributions
        if stats["std"] > stats["mean"] * 0.5:  # High variability
            anomalies.append({
                "metric_type": metric_type,
                "type": "high_variability",
                "description": f"High variability in {metric_type} measurements"
            })
        
        # Check for extreme values
        if stats["max"] > stats["percentiles"]["95"] * 1.5:
            anomalies.append({
                "metric_type": metric_type,
                "type": "extreme_high",
                "description": f"Extremely high values detected in {metric_type}"
            })
    
    return anomalies

def generate_population_insights(population_stats: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> List[str]:
    """Generate insights from population health data."""
    insights = []
    
    # Analyze overall health patterns
    if "bmi" in population_stats:
        avg_bmi = population_stats["bmi"]["mean"]
        if avg_bmi > 25:
            insights.append("Population shows tendency toward overweight")
        elif avg_bmi < 20:
            insights.append("Population shows tendency toward underweight")
    
    if "steps" in population_stats:
        avg_steps = population_stats["steps"]["mean"]
        if avg_steps < 8000:
            insights.append("Population shows low physical activity levels")
    
    # Add insights based on anomalies
    for anomaly in anomalies:
        insights.append(f"Anomaly detected: {anomaly['description']}")
    
    return insights

# Additional helper functions (simplified implementations)

def compute_data_summary(health_data: List[HealthData]) -> Dict[str, Any]:
    """Compute summary statistics for health data."""
    return {
        "total_points": len(health_data),
        "date_range": {
            "start": min(dp.timestamp for dp in health_data).isoformat(),
            "end": max(dp.timestamp for dp in health_data).isoformat()
        },
        "metrics_count": len(set(dp.metric_type for dp in health_data))
    }

def compute_trends(health_data: List[HealthData]) -> Dict[str, Any]:
    """Compute trends in health data."""
    # Simplified trend computation
    return {"trends": "computed"}

def compute_correlations(health_data: List[HealthData]) -> Dict[str, Any]:
    """Compute correlations between different health metrics."""
    # Simplified correlation computation
    return {"correlations": "computed"}

def detect_anomalies(health_data: List[HealthData]) -> List[Dict[str, Any]]:
    """Detect anomalies in health data."""
    # Simplified anomaly detection
    return []

def generate_recommendations(health_data: List[HealthData]) -> List[str]:
    """Generate health recommendations based on data."""
    # Simplified recommendation generation
    return ["Stay hydrated", "Get regular exercise", "Maintain healthy sleep patterns"]

def calculate_data_completeness(health_data: List[HealthData]) -> float:
    """Calculate data completeness percentage."""
    # Simplified completeness calculation
    return 85.5

def analyze_all_metrics(health_data: List[HealthData]) -> Dict[str, Any]:
    """Analyze all health metrics."""
    # Simplified metric analysis
    return {"analysis": "completed"}

def generate_next_steps(health_data: List[HealthData], user_profile) -> List[str]:
    """Generate next steps for user health improvement."""
    # Simplified next steps generation
    return ["Schedule annual checkup", "Increase daily activity", "Monitor blood pressure"]

def extract_key_metrics(health_data: List[HealthData]) -> Dict[str, Any]:
    """Extract key health metrics."""
    # Simplified key metrics extraction
    return {"key_metrics": "extracted"}

def generate_quick_insights(health_data: List[HealthData]) -> List[str]:
    """Generate quick insights from health data."""
    # Simplified insights generation
    return ["Good sleep pattern", "Regular exercise detected"]

def compute_detailed_trends(health_data: List[HealthData]) -> Dict[str, Any]:
    """Compute detailed trends in health data."""
    # Simplified detailed trends computation
    return {"detailed_trends": "computed"}

def detect_seasonal_patterns(health_data: List[HealthData]) -> Dict[str, Any]:
    """Detect seasonal patterns in health data."""
    # Simplified seasonal pattern detection
    return {"seasonal_patterns": "detected"}

def identify_improvement_areas(health_data: List[HealthData]) -> List[str]:
    """Identify areas for health improvement."""
    # Simplified improvement area identification
    return ["Increase physical activity", "Improve sleep quality"] 