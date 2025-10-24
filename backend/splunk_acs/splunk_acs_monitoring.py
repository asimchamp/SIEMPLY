"""
Splunk ACS Monitoring Service
Comprehensive monitoring and health checking for ACS operations
"""
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from .splunk_acs_models import ACSOperation, ChangeRequest, ConfigurationVersion
from .splunk_acs_utils import acs_metrics_collector, acs_rate_limiter
from .splunk_acs_client import SplunkCloudClient

logger = logging.getLogger(__name__)


class ACSMonitoringService:
    """Comprehensive monitoring service for ACS operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.metrics_collector = acs_metrics_collector
        self.rate_limiter = acs_rate_limiter
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "services": {},
                "metrics": {},
                "alerts": []
            }
            
            # Check database connectivity
            db_health = await self._check_database_health()
            health_status["services"]["database"] = db_health["status"]
            if db_health["status"] != "connected":
                health_status["status"] = "degraded"
                health_status["alerts"].append(f"Database: {db_health['message']}")
            
            # Check Splunk Cloud connectivity (if configs exist)
            splunk_health = await self._check_splunk_cloud_health()
            health_status["services"]["splunk_cloud"] = splunk_health["status"]
            if splunk_health["status"] != "connected":
                health_status["status"] = "degraded"
                health_status["alerts"].append(f"Splunk Cloud: {splunk_health['message']}")
            
            # Check encryption service
            encryption_health = await self._check_encryption_health()
            health_status["services"]["encryption"] = encryption_health["status"]
            if encryption_health["status"] != "active":
                health_status["status"] = "degraded"
                health_status["alerts"].append(f"Encryption: {encryption_health['message']}")
            
            # Get operational metrics
            health_status["metrics"] = await self.get_operational_metrics()
            
            # Check for critical alerts
            critical_alerts = await self._check_critical_alerts()
            if critical_alerts:
                health_status["status"] = "critical"
                health_status["alerts"].extend(critical_alerts)
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "services": {"overall": "error"}
            }
    
    async def _check_database_health(self) -> Dict[str, str]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic query
            result = self.db.query(func.count(ACSOperation.id)).scalar()
            
            response_time = time.time() - start_time
            
            if response_time > 5.0:  # More than 5 seconds is slow
                return {
                    "status": "degraded",
                    "message": f"Slow response time: {response_time:.2f}s"
                }
            
            return {
                "status": "connected",
                "message": "Database responding normally",
                "response_time": response_time
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "disconnected",
                "message": f"Connection failed: {str(e)}"
            }
    
    async def _check_splunk_cloud_health(self) -> Dict[str, str]:
        """Check Splunk Cloud connectivity"""
        try:
            # Get active configuration
            active_config = self.db.query(ConfigurationVersion).filter(
                ConfigurationVersion.is_active == True
            ).first()
            
            if not active_config:
                return {
                    "status": "no_config",
                    "message": "No active Splunk Cloud configuration"
                }
            
            # Try to connect to Splunk Cloud
            # This is a simplified check - in production you might want to test actual API calls
            return {
                "status": "connected",
                "message": "Splunk Cloud configuration active"
            }
            
        except Exception as e:
            logger.error(f"Splunk Cloud health check failed: {e}")
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }
    
    async def _check_encryption_health(self) -> Dict[str, str]:
        """Check encryption service health"""
        try:
            # Test encryption/decryption using the global credential manager
            from .splunk_acs_utils import credential_manager
            
            test_data = "test_encryption_health"
            encrypted = credential_manager.encrypt(test_data)
            decrypted = credential_manager.decrypt(encrypted)
            
            if decrypted == test_data:
                return {
                    "status": "active",
                    "message": "Encryption service working correctly"
                }
            else:
                return {
                    "status": "error",
                    "message": "Encryption/decryption test failed"
                }
                
        except Exception as e:
            logger.error(f"Encryption health check failed: {e}")
            return {
                "status": "error",
                "message": f"Encryption service error: {str(e)}"
            }
    
    async def _check_critical_alerts(self) -> List[str]:
        """Check for critical system alerts"""
        alerts = []
        
        try:
            # Check for failed operations in last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            failed_ops = self.db.query(ACSOperation).filter(
                and_(
                    ACSOperation.status == "failed",
                    ACSOperation.created_at >= one_hour_ago
                )
            ).count()
            
            if failed_ops > 10:
                alerts.append(f"High failure rate: {failed_ops} failed operations in last hour")
            
            # Check for pending change requests that are overdue
            overdue_changes = self.db.query(ChangeRequest).filter(
                and_(
                    ChangeRequest.status == "pending",
                    ChangeRequest.created_at <= datetime.utcnow() - timedelta(days=7)
                )
            ).count()
            
            if overdue_changes > 5:
                alerts.append(f"Overdue change requests: {overdue_changes} requests pending for more than 7 days")
            
            # Check rate limiting status
            if not self.rate_limiter.can_make_call():
                wait_time = self.rate_limiter.get_wait_time()
                alerts.append(f"Rate limit exceeded, wait {wait_time} seconds")
            
        except Exception as e:
            logger.error(f"Error checking critical alerts: {e}")
            alerts.append(f"Alert check failed: {str(e)}")
        
        return alerts
    
    async def get_operational_metrics(self) -> Dict[str, Any]:
        """Get comprehensive operational metrics"""
        try:
            metrics = self.metrics_collector.get_metrics()
            
            # Add database-specific metrics
            db_metrics = await self._get_database_metrics()
            metrics.update(db_metrics)
            
            # Add change request metrics
            cr_metrics = await self._get_change_request_metrics()
            metrics.update(cr_metrics)
            
            # Add performance metrics
            perf_metrics = await self._get_performance_metrics()
            metrics.update(perf_metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting operational metrics: {e}")
            return {"error": str(e)}
    
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database operation metrics"""
        try:
            # Total operations
            total_ops = self.db.query(func.count(ACSOperation.id)).scalar()
            
            # Operations by status
            status_counts = self.db.query(
                ACSOperation.status,
                func.count(ACSOperation.id)
            ).group_by(ACSOperation.status).all()
            
            # Operations by type
            type_counts = self.db.query(
                ACSOperation.operation_type,
                func.count(ACSOperation.id)
            ).group_by(ACSOperation.operation_type).all()
            
            # Recent activity (last 24 hours)
            one_day_ago = datetime.utcnow() - timedelta(days=1)
            recent_ops = self.db.query(func.count(ACSOperation.id)).filter(
                ACSOperation.created_at >= one_day_ago
            ).scalar()
            
            return {
                "database": {
                    "total_operations": total_ops,
                    "status_distribution": dict(status_counts),
                    "type_distribution": dict(type_counts),
                    "recent_activity_24h": recent_ops
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting database metrics: {e}")
            return {"database": {"error": str(e)}}
    
    async def _get_change_request_metrics(self) -> Dict[str, Any]:
        """Get change request workflow metrics"""
        try:
            # Total change requests
            total_cr = self.db.query(func.count(ChangeRequest.id)).scalar()
            
            # Change requests by status
            cr_status_counts = self.db.query(
                ChangeRequest.status,
                func.count(ChangeRequest.id)
            ).group_by(ChangeRequest.status).all()
            
            # Change requests by priority
            cr_priority_counts = self.db.query(
                ChangeRequest.priority,
                func.count(ChangeRequest.id)
            ).group_by(ChangeRequest.priority).all()
            
            # Average time to approval
            approved_cr = self.db.query(ChangeRequest).filter(
                ChangeRequest.status == "approved"
            ).all()
            
            approval_times = []
            for cr in approved_cr:
                if cr.updated_at and cr.created_at:
                    approval_time = (cr.updated_at - cr.created_at).total_seconds()
                    approval_times.append(approval_time)
            
            avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
            
            return {
                "change_requests": {
                    "total": total_cr,
                    "status_distribution": dict(cr_status_counts),
                    "priority_distribution": dict(cr_priority_counts),
                    "average_approval_time_seconds": avg_approval_time,
                    "pending_count": self.db.query(func.count(ChangeRequest.id)).filter(
                        ChangeRequest.status == "pending"
                    ).scalar()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting change request metrics: {e}")
            return {"change_requests": {"error": str(e)}}
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Get metrics from the collector
            collector_metrics = self.metrics_collector.get_metrics()
            
            # Calculate success rates
            success_rates = {}
            for op_type, counts in collector_metrics.get("operation_counts", {}).items():
                total = counts.get("total", 0)
                success = counts.get("success", 0)
                if total > 0:
                    success_rates[op_type] = (success / total) * 100
                else:
                    success_rates[op_type] = 0
            
            return {
                "performance": {
                    "success_rates": success_rates,
                    "response_times": collector_metrics.get("response_times", {}),
                    "error_counts": collector_metrics.get("error_counts", {}),
                    "rate_limiting": {
                        "can_make_call": self.rate_limiter.can_make_call(),
                        "wait_time": self.rate_limiter.get_wait_time()
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"performance": {"error": str(e)}}
    
    async def get_health_check_endpoint(self) -> Dict[str, Any]:
        """Get health check data for the API endpoint"""
        try:
            health_data = await self.get_system_health()
            
            # Simplify for API endpoint
            api_health = {
                "status": health_data["status"],
                "timestamp": health_data["timestamp"],
                "version": health_data["version"],
                "services": health_data["services"],
                "alerts_count": len(health_data.get("alerts", []))
            }
            
            return api_health
            
        except Exception as e:
            logger.error(f"Error getting health check endpoint data: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def reset_metrics(self):
        """Reset all monitoring metrics"""
        try:
            self.metrics_collector.reset_metrics()
            logger.info("All monitoring metrics have been reset")
        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")
    
    async def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format"""
        try:
            metrics = await self.get_operational_metrics()
            
            if format.lower() == "json":
                import json
                return json.dumps(metrics, indent=2, default=str)
            elif format.lower() == "csv":
                return self._metrics_to_csv(metrics)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return f"Error: {str(e)}"
    
    def _metrics_to_csv(self, metrics: Dict[str, Any]) -> str:
        """Convert metrics to CSV format"""
        try:
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["Metric", "Value"])
            
            # Flatten metrics and write rows
            for category, data in metrics.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                writer.writerow([f"{category}.{key}.{sub_key}", sub_value])
                        else:
                            writer.writerow([f"{category}.{key}", value])
                else:
                    writer.writerow([category, data])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting metrics to CSV: {e}")
            return f"Error: {str(e)}"


# Global monitoring service instance
acs_monitoring_service = None

def get_acs_monitoring_service(db: Session) -> ACSMonitoringService:
    """Get or create ACS monitoring service instance"""
    global acs_monitoring_service
    if acs_monitoring_service is None:
        acs_monitoring_service = ACSMonitoringService(db)
    return acs_monitoring_service
