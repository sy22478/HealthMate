"""
Database Constraints and Validations for HealthMate

This module provides database constraints, validations, and data integrity checks
for the HealthMate application.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import text, inspect, CheckConstraint, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import Session, validates
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date
import re
import json

logger = logging.getLogger(__name__)

class DatabaseConstraints:
    """Database constraints management class."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.inspector = inspect(self.db.bind)
    
    def get_table_constraints(self, table_name: str) -> Dict[str, Any]:
        """
        Get all constraints for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary containing table constraints
        """
        try:
            constraints = {
                'primary_keys': self.inspector.get_pk_constraint(table_name),
                'foreign_keys': self.inspector.get_foreign_keys(table_name),
                'unique_constraints': self.inspector.get_unique_constraints(table_name),
                'check_constraints': self.inspector.get_check_constraints(table_name),
                'indexes': self.inspector.get_indexes(table_name)
            }
            
            return {
                'table_name': table_name,
                'constraints': constraints
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting constraints for table {table_name}: {e}")
            return {'error': str(e)}
    
    def validate_data_integrity(self, table_name: str) -> Dict[str, Any]:
        """
        Validate data integrity for a specific table.
        
        Args:
            table_name: Name of the table to validate
            
        Returns:
            Validation results
        """
        try:
            validation_results = {
                'table_name': table_name,
                'checks': [],
                'errors': [],
                'warnings': []
            }
            
            # Check for null values in non-nullable columns
            null_check = self._check_null_constraints(table_name)
            validation_results['checks'].extend(null_check)
            
            # Check for duplicate values in unique columns
            duplicate_check = self._check_unique_constraints(table_name)
            validation_results['checks'].extend(duplicate_check)
            
            # Check foreign key integrity
            fk_check = self._check_foreign_key_integrity(table_name)
            validation_results['checks'].extend(fk_check)
            
            # Check data format and range constraints
            format_check = self._check_data_format_constraints(table_name)
            validation_results['checks'].extend(format_check)
            
            # Categorize results
            for check in validation_results['checks']:
                if check['status'] == 'error':
                    validation_results['errors'].append(check)
                elif check['status'] == 'warning':
                    validation_results['warnings'].append(check)
            
            return validation_results
            
        except SQLAlchemyError as e:
            logger.error(f"Error validating data integrity for table {table_name}: {e}")
            return {'error': str(e)}
    
    def _check_null_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Check for null values in non-nullable columns."""
        checks = []
        
        try:
            # Get table columns
            columns = self.inspector.get_columns(table_name)
            
            for column in columns:
                if not column.get('nullable', True):  # Non-nullable column
                    column_name = column['name']
                    
                    # Check for null values
                    query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL")
                    result = self.db.execute(query)
                    null_count = result.scalar()
                    
                    if null_count > 0:
                        checks.append({
                            'type': 'null_constraint',
                            'column': column_name,
                            'status': 'error',
                            'message': f'Found {null_count} null values in non-nullable column {column_name}',
                            'count': null_count
                        })
                    else:
                        checks.append({
                            'type': 'null_constraint',
                            'column': column_name,
                            'status': 'pass',
                            'message': f'No null values found in column {column_name}'
                        })
            
        except SQLAlchemyError as e:
            logger.error(f"Error checking null constraints: {e}")
        
        return checks
    
    def _check_unique_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Check for duplicate values in unique columns."""
        checks = []
        
        try:
            # Get unique constraints
            unique_constraints = self.inspector.get_unique_constraints(table_name)
            
            for constraint in unique_constraints:
                columns = constraint['column_names']
                constraint_name = constraint['name']
                
                # Build query to find duplicates
                columns_str = ', '.join(columns)
                query = text(f"""
                    SELECT {columns_str}, COUNT(*) as count
                    FROM {table_name}
                    GROUP BY {columns_str}
                    HAVING COUNT(*) > 1
                """)
                
                result = self.db.execute(query)
                duplicates = result.fetchall()
                
                if duplicates:
                    total_duplicates = sum(row.count for row in duplicates)
                    checks.append({
                        'type': 'unique_constraint',
                        'constraint': constraint_name,
                        'columns': columns,
                        'status': 'error',
                        'message': f'Found {total_duplicates} duplicate values in unique constraint {constraint_name}',
                        'duplicates': [dict(zip(columns + ['count'], row)) for row in duplicates]
                    })
                else:
                    checks.append({
                        'type': 'unique_constraint',
                        'constraint': constraint_name,
                        'columns': columns,
                        'status': 'pass',
                        'message': f'No duplicates found in unique constraint {constraint_name}'
                    })
            
        except SQLAlchemyError as e:
            logger.error(f"Error checking unique constraints: {e}")
        
        return checks
    
    def _check_foreign_key_integrity(self, table_name: str) -> List[Dict[str, Any]]:
        """Check foreign key integrity."""
        checks = []
        
        try:
            # Get foreign key constraints
            foreign_keys = self.inspector.get_foreign_keys(table_name)
            
            for fk in foreign_keys:
                local_columns = fk['constrained_columns']
                referred_table = fk['referred_table']
                referred_columns = fk['referred_columns']
                
                # Build query to find orphaned records
                local_columns_str = ', '.join(local_columns)
                referred_columns_str = ', '.join(referred_columns)
                
                query = text(f"""
                    SELECT COUNT(*) FROM {table_name} t
                    LEFT JOIN {referred_table} r ON {' AND '.join([f't.{lc} = r.{rc}' for lc, rc in zip(local_columns, referred_columns)])}
                    WHERE r.{referred_columns[0]} IS NULL
                """)
                
                result = self.db.execute(query)
                orphaned_count = result.scalar()
                
                if orphaned_count > 0:
                    checks.append({
                        'type': 'foreign_key_integrity',
                        'local_table': table_name,
                        'referred_table': referred_table,
                        'local_columns': local_columns,
                        'referred_columns': referred_columns,
                        'status': 'error',
                        'message': f'Found {orphaned_count} orphaned records in foreign key relationship',
                        'count': orphaned_count
                    })
                else:
                    checks.append({
                        'type': 'foreign_key_integrity',
                        'local_table': table_name,
                        'referred_table': referred_table,
                        'local_columns': local_columns,
                        'referred_columns': referred_columns,
                        'status': 'pass',
                        'message': f'Foreign key integrity maintained for {referred_table}'
                    })
            
        except SQLAlchemyError as e:
            logger.error(f"Error checking foreign key integrity: {e}")
        
        return checks
    
    def _check_data_format_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Check data format and range constraints."""
        checks = []
        
        try:
            # Define format checks for different tables
            format_checks = {
                'users': [
                    {
                        'column': 'email',
                        'type': 'email_format',
                        'query': "SELECT COUNT(*) FROM users WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'"
                    },
                    {
                        'column': 'age',
                        'type': 'range_check',
                        'query': "SELECT COUNT(*) FROM users WHERE age < 0 OR age > 150"
                    }
                ],
                'health_data': [
                    {
                        'column': 'confidence',
                        'type': 'range_check',
                        'query': "SELECT COUNT(*) FROM health_data WHERE confidence < 0.0 OR confidence > 1.0"
                    }
                ],
                'symptom_logs': [
                    {
                        'column': 'pain_level',
                        'type': 'range_check',
                        'query': "SELECT COUNT(*) FROM symptom_logs WHERE pain_level < 0 OR pain_level > 10"
                    },
                    {
                        'column': 'severity',
                        'type': 'enum_check',
                        'query': "SELECT COUNT(*) FROM symptom_logs WHERE severity NOT IN ('mild', 'moderate', 'severe')"
                    }
                ],
                'medication_logs': [
                    {
                        'column': 'effectiveness',
                        'type': 'range_check',
                        'query': "SELECT COUNT(*) FROM medication_logs WHERE effectiveness < 1 OR effectiveness > 10"
                    }
                ],
                'health_goals': [
                    {
                        'column': 'progress',
                        'type': 'range_check',
                        'query': "SELECT COUNT(*) FROM health_goals WHERE progress < 0.0 OR progress > 100.0"
                    }
                ],
                'health_alerts': [
                    {
                        'column': 'severity',
                        'type': 'enum_check',
                        'query': "SELECT COUNT(*) FROM health_alerts WHERE severity NOT IN ('mild', 'moderate', 'severe')"
                    }
                ]
            }
            
            table_checks = format_checks.get(table_name, [])
            
            for check in table_checks:
                query = text(check['query'])
                result = self.db.execute(query)
                invalid_count = result.scalar()
                
                if invalid_count > 0:
                    checks.append({
                        'type': check['type'],
                        'column': check['column'],
                        'status': 'error',
                        'message': f'Found {invalid_count} records with invalid {check["type"]} in column {check["column"]}',
                        'count': invalid_count
                    })
                else:
                    checks.append({
                        'type': check['type'],
                        'column': check['column'],
                        'status': 'pass',
                        'message': f'All records have valid {check["type"]} in column {check["column"]}'
                    })
            
        except SQLAlchemyError as e:
            logger.error(f"Error checking data format constraints: {e}")
        
        return checks

class DataValidators:
    """Data validation utilities."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email:
            return False
        
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid phone number (7-15 digits)
        return 7 <= len(digits_only) <= 15
    
    @staticmethod
    def validate_date_of_birth(dob: str) -> bool:
        """Validate date of birth."""
        if not dob:
            return False
        
        try:
            # Try to parse the date
            parsed_date = datetime.strptime(dob, '%Y-%m-%d').date()
            today = date.today()
            
            # Check if date is in the past and reasonable (not more than 150 years ago)
            if parsed_date > today:
                return False
            
            age = today.year - parsed_date.year
            if age > 150:
                return False
            
            return True
            
        except ValueError:
            return False
    
    @staticmethod
    def validate_json_field(json_str: str) -> bool:
        """Validate JSON field format."""
        if not json_str:
            return True  # Empty JSON is valid
        
        try:
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def validate_health_metric_value(value: Union[str, int, float], data_type: str) -> bool:
        """Validate health metric values based on data type."""
        if value is None:
            return False
        
        try:
            if data_type == 'blood_pressure':
                # Blood pressure should be a positive number
                return float(value) > 0
            
            elif data_type == 'heart_rate':
                # Heart rate should be between 30 and 250 bpm
                hr = float(value)
                return 30 <= hr <= 250
            
            elif data_type == 'weight':
                # Weight should be positive and reasonable (10-500 kg)
                weight = float(value)
                return 10 <= weight <= 500
            
            elif data_type == 'height':
                # Height should be positive and reasonable (50-300 cm)
                height = float(value)
                return 50 <= height <= 300
            
            elif data_type == 'temperature':
                # Temperature should be reasonable (30-45°C)
                temp = float(value)
                return 30 <= temp <= 45
            
            elif data_type == 'blood_sugar':
                # Blood sugar should be positive and reasonable (20-800 mg/dL)
                bs = float(value)
                return 20 <= bs <= 800
            
            else:
                # For unknown types, just check if it's a number
                return isinstance(value, (int, float)) or str(value).replace('.', '').isdigit()
                
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_medication_dosage(dosage: str) -> bool:
        """Validate medication dosage format."""
        if not dosage:
            return False
        
        # Basic dosage pattern: number + unit (e.g., "10mg", "5ml", "2 tablets")
        pattern = r'^\d+(\.\d+)?\s*(mg|ml|g|mcg|tablets?|capsules?|drops?|units?)$'
        return bool(re.match(pattern, dosage.lower()))
    
    @staticmethod
    def validate_frequency(frequency: str) -> bool:
        """Validate medication frequency format."""
        if not frequency:
            return False
        
        # Common frequency patterns
        patterns = [
            r'^\d+\s*(times?|doses?)\s*(daily|per day|a day)$',
            r'^(once|twice|thrice)\s*(daily|per day|a day)$',
            r'^every\s*\d+\s*(hours?|days?|weeks?|months?)$',
            r'^(as needed|prn|when required)$'
        ]
        
        return any(re.match(pattern, frequency.lower()) for pattern in patterns)

class ConstraintEnforcement:
    """Constraint enforcement utilities."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def enforce_user_constraints(self, user_data: Dict[str, Any]) -> List[str]:
        """Enforce constraints for user data."""
        errors = []
        
        # Email validation
        if 'email' in user_data and not DataValidators.validate_email(user_data['email']):
            errors.append("Invalid email format")
        
        # Phone validation
        if 'phone' in user_data and user_data['phone'] and not DataValidators.validate_phone(user_data['phone']):
            errors.append("Invalid phone number format")
        
        # Date of birth validation
        if 'date_of_birth' in user_data and user_data['date_of_birth'] and not DataValidators.validate_date_of_birth(user_data['date_of_birth']):
            errors.append("Invalid date of birth")
        
        # Age validation
        if 'age' in user_data:
            age = user_data['age']
            if not isinstance(age, int) or age < 0 or age > 150:
                errors.append("Age must be between 0 and 150")
        
        # Role validation
        if 'role' in user_data:
            valid_roles = ['patient', 'doctor', 'admin', 'researcher']
            if user_data['role'] not in valid_roles:
                errors.append(f"Role must be one of: {', '.join(valid_roles)}")
        
        return errors
    
    def enforce_health_data_constraints(self, health_data: Dict[str, Any]) -> List[str]:
        """Enforce constraints for health data."""
        errors = []
        
        # Data type validation
        valid_types = [
            'blood_pressure', 'heart_rate', 'weight', 'height', 'temperature',
            'blood_sugar', 'cholesterol', 'oxygen_saturation', 'respiratory_rate',
            'pain_level', 'sleep_hours', 'steps', 'calories_burned'
        ]
        
        if 'data_type' in health_data and health_data['data_type'] not in valid_types:
            errors.append(f"Invalid data type. Must be one of: {', '.join(valid_types)}")
        
        # Value validation
        if 'value' in health_data and 'data_type' in health_data:
            if not DataValidators.validate_health_metric_value(health_data['value'], health_data['data_type']):
                errors.append(f"Invalid value for data type {health_data['data_type']}")
        
        # Confidence validation
        if 'confidence' in health_data:
            confidence = health_data['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                errors.append("Confidence must be between 0.0 and 1.0")
        
        return errors
    
    def enforce_medication_constraints(self, medication_data: Dict[str, Any]) -> List[str]:
        """Enforce constraints for medication data."""
        errors = []
        
        # Dosage validation
        if 'dosage' in medication_data and not DataValidators.validate_medication_dosage(medication_data['dosage']):
            errors.append("Invalid medication dosage format")
        
        # Frequency validation
        if 'frequency' in medication_data and not DataValidators.validate_frequency(medication_data['frequency']):
            errors.append("Invalid medication frequency format")
        
        # Effectiveness validation
        if 'effectiveness' in medication_data:
            effectiveness = medication_data['effectiveness']
            if not isinstance(effectiveness, int) or effectiveness < 1 or effectiveness > 10:
                errors.append("Effectiveness must be between 1 and 10")
        
        return errors
    
    def enforce_symptom_constraints(self, symptom_data: Dict[str, Any]) -> List[str]:
        """Enforce constraints for symptom data."""
        errors = []
        
        # Severity validation
        if 'severity' in symptom_data:
            valid_severities = ['mild', 'moderate', 'severe']
            if symptom_data['severity'] not in valid_severities:
                errors.append(f"Severity must be one of: {', '.join(valid_severities)}")
        
        # Pain level validation
        if 'pain_level' in symptom_data:
            pain_level = symptom_data['pain_level']
            if not isinstance(pain_level, int) or pain_level < 0 or pain_level > 10:
                errors.append("Pain level must be between 0 and 10")
        
        return errors
    
    def enforce_health_goal_constraints(self, goal_data: Dict[str, Any]) -> List[str]:
        """Enforce constraints for health goal data."""
        errors = []
        
        # Progress validation
        if 'progress' in goal_data:
            progress = goal_data['progress']
            if not isinstance(progress, (int, float)) or progress < 0.0 or progress > 100.0:
                errors.append("Progress must be between 0.0 and 100.0")
        
        # Goal type validation
        valid_types = [
            'weight_loss', 'weight_gain', 'blood_pressure', 'heart_rate',
            'blood_sugar', 'exercise', 'sleep', 'meditation', 'water_intake'
        ]
        
        if 'goal_type' in goal_data and goal_data['goal_type'] not in valid_types:
            errors.append(f"Goal type must be one of: {', '.join(valid_types)}")
        
        return errors

# Utility function to run comprehensive constraint validation
def validate_database_integrity(db_session: Session) -> Dict[str, Any]:
    """
    Run comprehensive database integrity validation.
    
    Args:
        db_session: Database session
        
    Returns:
        Complete validation results
    """
    constraints = DatabaseConstraints(db_session)
    
    validation_results = {
        'timestamp': datetime.utcnow().isoformat(),
        'tables': {},
        'overall_status': 'pass',
        'total_errors': 0,
        'total_warnings': 0
    }
    
    # Validate all tables
    tables = ['users', 'health_data', 'symptom_logs', 'medication_logs', 
             'health_goals', 'health_alerts', 'conversations']
    
    for table in tables:
        table_results = constraints.validate_data_integrity(table)
        validation_results['tables'][table] = table_results
        
        # Count errors and warnings
        if 'errors' in table_results:
            validation_results['total_errors'] += len(table_results['errors'])
        if 'warnings' in table_results:
            validation_results['total_warnings'] += len(table_results['warnings'])
    
    # Set overall status
    if validation_results['total_errors'] > 0:
        validation_results['overall_status'] = 'error'
    elif validation_results['total_warnings'] > 0:
        validation_results['overall_status'] = 'warning'
    
    return validation_results 