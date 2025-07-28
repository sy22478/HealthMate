"""
Compliance Router for HealthMate

This router provides API endpoints for:
- HIPAA compliance checking
- GDPR compliance management
- Data export (GDPR Article 20)
- Data deletion (GDPR Article 17)
- Compliance reporting
- Data retention management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.services.auth import get_current_user
from app.services.compliance_service import (
    ComplianceService, DataCategory, ComplianceLevel, 
    RetentionPolicy, DataRetentionRule, ComplianceReport
)
from app.models.user import User
from app.utils.audit_logging import AuditLogger
from app.utils.rate_limiting import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Pydantic models for request/response
class ComplianceCheckRequest(BaseModel):
    user_id: Optional[int] = None
    compliance_level: ComplianceLevel = ComplianceLevel.HIPAA

class DataExportRequest(BaseModel):
    format: str = "json"
    include_health_data: bool = True
    include_conversations: bool = True
    include_analytics: bool = False

class DataDeletionRequest(BaseModel):
    data_categories: List[DataCategory]
    confirm_deletion: bool = False
    archive_before_delete: bool = True

class ComplianceReportRequest(BaseModel):
    report_type: str = "monthly"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_recommendations: bool = True

class RetentionPolicyUpdate(BaseModel):
    category: DataCategory
    policy: RetentionPolicy
    auto_cleanup: bool = True
    notify_before_deletion: bool = True
    notification_days: int = 30

@router.get("/hipaa-compliance")
@rate_limit(max_requests=10, window_seconds=300)  # 10 requests per 5 minutes
async def check_hipaa_compliance(
    user_id: Optional[int] = Query(None, description="Specific user ID to check"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check HIPAA compliance for the system or specific user.
    
    This endpoint performs comprehensive HIPAA compliance checks including:
    - Data encryption verification
    - Access control validation
    - Audit logging assessment
    - Data retention policy compliance
    - Breach protection measures
    - User consent management
    """
    try:
        # Get current user (admin required for system-wide checks)
        current_user = await get_current_user(credentials.credentials, db)
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Perform HIPAA compliance check
        compliance_result = await compliance_service.check_hipaa_compliance(user_id)
        
        # Log the compliance check
        AuditLogger.log_api_call(
            method="GET",
            path="/compliance/hipaa-compliance",
            user_id=current_user.id,
            user_email=current_user.email,
            success=True,
            details={
                "target_user_id": user_id,
                "compliance_score": compliance_result.get("compliance_score", 0),
                "compliant": compliance_result.get("compliant", False)
            }
        )
        
        return {
            "success": True,
            "data": compliance_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"HIPAA compliance check failed: {e}")
        AuditLogger.log_api_call(
            method="GET",
            path="/compliance/hipaa-compliance",
            user_id=current_user.id if 'current_user' in locals() else None,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"HIPAA compliance check failed: {str(e)}"
        )

@router.get("/gdpr-compliance")
@rate_limit(max_requests=10, window_seconds=300)
async def check_gdpr_compliance(
    user_id: Optional[int] = Query(None, description="Specific user ID to check"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Check GDPR compliance for the system or specific user.
    
    This endpoint performs comprehensive GDPR compliance checks including:
    - Data portability implementation
    - Right to be forgotten functionality
    - Consent management verification
    - Data minimization assessment
    - Breach notification procedures
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Perform GDPR compliance check
        compliance_result = await compliance_service.check_gdpr_compliance(user_id)
        
        # Log the compliance check
        AuditLogger.log_api_call(
            method="GET",
            path="/compliance/gdpr-compliance",
            user_id=current_user.id,
            user_email=current_user.email,
            success=True,
            details={
                "target_user_id": user_id,
                "compliance_score": compliance_result.get("compliance_score", 0),
                "compliant": compliance_result.get("compliant", False)
            }
        )
        
        return {
            "success": True,
            "data": compliance_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"GDPR compliance check failed: {e}")
        AuditLogger.log_api_call(
            method="GET",
            path="/compliance/gdpr-compliance",
            user_id=current_user.id if 'current_user' in locals() else None,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GDPR compliance check failed: {str(e)}"
        )

@router.post("/export-data")
@rate_limit(max_requests=5, window_seconds=3600)  # 5 requests per hour
async def export_user_data(
    request: DataExportRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export user data in compliance with GDPR Article 20 (Right to Data Portability).
    
    This endpoint allows users to export their personal data in a structured,
    commonly used, and machine-readable format. The export includes:
    - Personal profile information
    - Health data records
    - Conversation history
    - Analytics data (if requested)
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Export user data
        export_data = await compliance_service.export_user_data(
            user_id=current_user.id,
            format=request.format
        )
        
        return {
            "success": True,
            "data": export_data,
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "format": request.format,
                "compliance": "gdpr_article_20",
                "user_id": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        AuditLogger.log_api_call(
            method="POST",
            path="/compliance/export-data",
            user_id=current_user.id if 'current_user' in locals() else None,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data export failed: {str(e)}"
        )

@router.post("/delete-data")
@rate_limit(max_requests=3, window_seconds=3600)  # 3 requests per hour
async def delete_user_data(
    request: DataDeletionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete user data in compliance with GDPR Article 17 (Right to be Forgotten).
    
    This endpoint allows users to request deletion of their personal data.
    The deletion is permanent and cannot be undone. Users must confirm
    the deletion explicitly.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Require explicit confirmation for deletion
        if not request.confirm_deletion:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deletion confirmation required. Set confirm_deletion to true."
            )
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Delete user data
        deletion_result = await compliance_service.delete_user_data(
            user_id=current_user.id,
            data_categories=request.data_categories
        )
        
        return {
            "success": True,
            "data": deletion_result,
            "message": "Data deletion completed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data deletion failed: {e}")
        AuditLogger.log_api_call(
            method="POST",
            path="/compliance/delete-data",
            user_id=current_user.id if 'current_user' in locals() else None,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data deletion failed: {str(e)}"
        )

@router.post("/generate-report")
@rate_limit(max_requests=5, window_seconds=3600)  # 5 requests per hour
async def generate_compliance_report(
    request: ComplianceReportRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate comprehensive compliance report.
    
    This endpoint generates detailed compliance reports including:
    - HIPAA compliance assessment
    - GDPR compliance verification
    - Audit summary
    - Data retention status
    - Security events
    - Compliance recommendations
    """
    try:
        # Get current user (admin required for reports)
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required for compliance reports"
            )
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Generate compliance report
        report = await compliance_service.generate_compliance_report(
            report_type=request.report_type,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Convert report to dict for JSON response
        report_dict = {
            "report_id": report.report_id,
            "report_type": report.report_type,
            "generated_at": report.generated_at.isoformat(),
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "compliance_score": report.compliance_score,
            "violations": report.violations,
            "recommendations": report.recommendations if request.include_recommendations else [],
            "data_retention_status": report.data_retention_status,
            "audit_summary": report.audit_summary,
            "security_events": report.security_events
        }
        
        # Log the report generation
        AuditLogger.log_api_call(
            method="POST",
            path="/compliance/generate-report",
            user_id=current_user.id,
            user_email=current_user.email,
            success=True,
            details={
                "report_id": report.report_id,
                "report_type": report.report_type,
                "compliance_score": report.compliance_score
            }
        )
        
        return {
            "success": True,
            "data": report_dict,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compliance report generation failed: {e}")
        AuditLogger.log_api_call(
            method="POST",
            path="/compliance/generate-report",
            user_id=current_user.id if 'current_user' in locals() else None,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance report generation failed: {str(e)}"
        )

@router.get("/retention-policies")
@rate_limit(max_requests=20, window_seconds=300)
async def get_retention_policies(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current data retention policies.
    
    Returns the configured data retention policies for all data categories
    including retention periods, compliance requirements, and cleanup settings.
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Get retention policies
        policies = []
        for category, rule in compliance_service.retention_rules.items():
            policies.append({
                "category": category.value,
                "policy": rule.policy.value,
                "description": rule.description,
                "compliance_requirements": [req.value for req in rule.compliance_requirements],
                "auto_cleanup": rule.auto_cleanup,
                "archive_before_delete": rule.archive_before_delete,
                "notify_before_deletion": rule.notify_before_deletion,
                "notification_days": rule.notification_days
            })
        
        return {
            "success": True,
            "data": {
                "policies": policies,
                "total_policies": len(policies)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get retention policies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get retention policies: {str(e)}"
        )

@router.put("/retention-policies")
@rate_limit(max_requests=10, window_seconds=3600)  # 10 requests per hour
async def update_retention_policy(
    request: RetentionPolicyUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Update data retention policy for a specific category.
    
    This endpoint allows administrators to modify retention policies
    for different data categories. Changes are logged for audit purposes.
    """
    try:
        # Get current user (admin required)
        current_user = await get_current_user(credentials.credentials, db)
        
        # Check if user has admin privileges
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to update retention policies"
            )
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Update retention policy
        if request.category in compliance_service.retention_rules:
            rule = compliance_service.retention_rules[request.category]
            rule.policy = request.policy
            rule.auto_cleanup = request.auto_cleanup
            rule.notify_before_deletion = request.notify_before_deletion
            rule.notification_days = request.notification_days
            
            # Log the policy update
            AuditLogger.log_api_call(
                method="PUT",
                path="/compliance/retention-policies",
                user_id=current_user.id,
                user_email=current_user.email,
                success=True,
                details={
                    "category": request.category.value,
                    "new_policy": request.policy.value,
                    "auto_cleanup": request.auto_cleanup,
                    "notify_before_deletion": request.notify_before_deletion,
                    "notification_days": request.notification_days
                }
            )
            
            return {
                "success": True,
                "message": f"Retention policy updated for {request.category.value}",
                "data": {
                    "category": request.category.value,
                    "policy": request.policy.value,
                    "auto_cleanup": request.auto_cleanup,
                    "notify_before_deletion": request.notify_before_deletion,
                    "notification_days": request.notification_days
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Retention policy not found for category: {request.category.value}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update retention policy: {e}")
        AuditLogger.log_api_call(
            method="PUT",
            path="/compliance/retention-policies",
            user_id=current_user.id if 'current_user' in locals() else None,
            success=False,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update retention policy: {str(e)}"
        )

@router.get("/compliance-status")
@rate_limit(max_requests=30, window_seconds=300)
async def get_compliance_status(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get overall compliance status summary.
    
    Returns a high-level overview of compliance status including:
    - HIPAA compliance score
    - GDPR compliance score
    - Overall compliance status
    - Recent compliance events
    """
    try:
        # Get current user
        current_user = await get_current_user(credentials.credentials, db)
        
        # Initialize compliance service
        compliance_service = ComplianceService(db)
        
        # Check both HIPAA and GDPR compliance
        hipaa_compliance = await compliance_service.check_hipaa_compliance()
        gdpr_compliance = await compliance_service.check_gdpr_compliance()
        
        # Calculate overall compliance score
        overall_score = (hipaa_compliance.get("compliance_score", 0) + 
                        gdpr_compliance.get("compliance_score", 0)) / 2
        
        return {
            "success": True,
            "data": {
                "overall_compliance_score": overall_score,
                "overall_status": "compliant" if overall_score >= 95 else "non_compliant",
                "hipaa": {
                    "compliant": hipaa_compliance.get("compliant", False),
                    "score": hipaa_compliance.get("compliance_score", 0)
                },
                "gdpr": {
                    "compliant": gdpr_compliance.get("compliant", False),
                    "score": gdpr_compliance.get("compliance_score", 0)
                },
                "last_updated": datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance status: {str(e)}"
        ) 