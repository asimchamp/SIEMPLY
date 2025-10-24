"""
Splunk ACS Workflow Engine
Manages change request workflow and approval processes
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from fastapi import HTTPException

from .splunk_acs_models import ChangeRequest, ApprovalWorkflow
from .splunk_acs_notifications import NotificationService

logger = logging.getLogger(__name__)


class ChangeRequestWorkflow:
    """Manages the complete change request lifecycle"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
    
    async def create_change_request(self, data: Dict[str, Any], user_id: int) -> ChangeRequest:
        """Create a new change request with approval workflow"""
        try:
            # Generate unique request ID (CR-2024-001 format)
            request_id = self._generate_request_id()
            
            # Create change request
            change_request = ChangeRequest(
                request_id=request_id,
                title=data['title'],
                description=data.get('description'),
                change_type=data['change_type'],
                priority=data.get('priority', 'medium'),
                requester_id=user_id,
                resource_type=data['resource_type'],
                resource_id=data.get('resource_id'),
                proposed_changes=data['proposed_changes'],
                risk_assessment=data.get('risk_assessment', 'low'),
                implementation_plan=data.get('implementation_plan'),
                rollback_plan=data.get('rollback_plan'),
                scheduled_date=data.get('scheduled_date')
            )
            
            self.db.add(change_request)
            self.db.commit()
            self.db.refresh(change_request)
            
            # Create multi-level approval workflow
            await self._create_approval_workflow(change_request.id, data)
            
            # Send notifications to approvers
            await self.notification_service.notify_change_request_created(change_request)
            
            logger.info(f"Created change request {request_id} for user {user_id}")
            return change_request
            
        except Exception as e:
            logger.error(f"Failed to create change request: {e}")
            raise HTTPException(status_code=500, detail="Failed to create change request")
    
    async def _create_approval_workflow(self, change_request_id: int, data: Dict[str, Any]):
        """Create approval workflow levels based on change type and priority"""
        try:
            workflows = []
            
            # Level 1: Team Lead approval (always required)
            workflow_level_1 = ApprovalWorkflow(
                change_request_id=change_request_id,
                level=1,
                approver_role="team_lead",
                status="pending"
            )
            workflows.append(workflow_level_1)
            
            # Level 2: Admin approval (for high priority or critical changes)
            if data.get('priority') in ['high', 'critical'] or data.get('change_type') == 'emergency':
                workflow_level_2 = ApprovalWorkflow(
                    change_request_id=change_request_id,
                    level=2,
                    approver_role="admin",
                    status="pending"
                )
                workflows.append(workflow_level_2)
            
            # Level 3: Security team approval (for security-related changes)
            if self._is_security_related_change(data):
                workflow_level_3 = ApprovalWorkflow(
                    change_request_id=change_request_id,
                    level=3,
                    approver_role="security_team",
                    status="pending"
                )
                workflows.append(workflow_level_3)
            
            # Add all workflows to database
            for workflow in workflows:
                self.db.add(workflow)
            
            self.db.commit()
            
            logger.info(f"Created {len(workflows)} approval workflow levels for change request {change_request_id}")
            
        except Exception as e:
            logger.error(f"Failed to create approval workflow: {e}")
            raise HTTPException(status_code=500, detail="Failed to create approval workflow")
    
    def _is_security_related_change(self, data: Dict[str, Any]) -> bool:
        """Determine if change is security-related"""
        security_keywords = [
            'ip_allow_list', 'firewall', 'authentication', 'authorization',
            'user', 'role', 'permission', 'token', 'security', 'access'
        ]
        
        resource_type = data.get('resource_type', '').lower()
        title = data.get('title', '').lower()
        description = data.get('description', '').lower()
        
        # Check if any security keywords are present
        for keyword in security_keywords:
            if (keyword in resource_type or 
                keyword in title or 
                keyword in description):
                return True
        
        return False
    
    def _generate_request_id(self) -> str:
        """Generate unique change request ID"""
        from datetime import datetime
        
        # Get current year
        current_year = datetime.now().year
        
        # Get count of requests for current year
        year_start = datetime(current_year, 1, 1)
        year_end = datetime(current_year, 12, 31, 23, 59, 59)
        
        count = self.db.query(ChangeRequest).filter(
            and_(
                ChangeRequest.created_at >= year_start,
                ChangeRequest.created_at <= year_end
            )
        ).count()
        
        # Format: CR-2024-001
        return f"CR-{current_year}-{count + 1:03d}"
    
    async def approve_change_request(self, request_id: str, level: int, approver_id: int, comments: str = None):
        """Approve a change request at a specific level"""
        try:
            # Get the change request
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.request_id == request_id
            ).first()
            
            if not change_request:
                raise HTTPException(status_code=404, detail="Change request not found")
            
            # Get the workflow level
            workflow = self.db.query(ApprovalWorkflow).filter(
                and_(
                    ApprovalWorkflow.change_request_id == change_request.id,
                    ApprovalWorkflow.level == level
                )
            ).first()
            
            if not workflow:
                raise HTTPException(status_code=404, detail=f"Approval workflow not found for level {level}")
            
            if workflow.status != "pending":
                raise HTTPException(status_code=400, detail=f"Workflow level {level} is not pending approval")
            
            # Approve the workflow level
            workflow.status = "approved"
            workflow.approver_id = approver_id
            workflow.approved_at = datetime.utcnow()
            workflow.comments = comments
            
            self.db.commit()
            
            # Check if all levels are approved
            if await self._all_levels_approved(change_request.id):
                await self._mark_change_request_approved(change_request.id)
            
            # Send notifications
            await self.notification_service.notify_approval_granted(workflow)
            
            logger.info(f"Approved change request {request_id} at level {level} by user {approver_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to approve change request {request_id} at level {level}: {e}")
            raise HTTPException(status_code=500, detail="Failed to approve change request")
    
    async def reject_change_request(self, request_id: str, level: int, approver_id: int, comments: str):
        """Reject a change request at a specific level"""
        try:
            # Get the change request
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.request_id == request_id
            ).first()
            
            if not change_request:
                raise HTTPException(status_code=404, detail="Change request not found")
            
            # Get the workflow level
            workflow = self.db.query(ApprovalWorkflow).filter(
                and_(
                    ApprovalWorkflow.change_request_id == change_request.id,
                    ApprovalWorkflow.level == level
                )
            ).first()
            
            if not workflow:
                raise HTTPException(status_code=404, detail=f"Approval workflow not found for level {level}")
            
            if workflow.status != "pending":
                raise HTTPException(status_code=400, detail=f"Workflow level {level} is not pending approval")
            
            # Reject the workflow level
            workflow.status = "rejected"
            workflow.approver_id = approver_id
            workflow.approved_at = datetime.utcnow()
            workflow.comments = comments
            
            # Mark change request as rejected
            change_request.status = "rejected"
            change_request.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Send notifications
            await self.notification_service.notify_approval_rejected(workflow)
            
            logger.info(f"Rejected change request {request_id} at level {level} by user {approver_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to reject change request {request_id} at level {level}: {e}")
            raise HTTPException(status_code=500, detail="Failed to reject change request")
    
    async def _all_levels_approved(self, change_request_id: int) -> bool:
        """Check if all workflow levels are approved"""
        try:
            # Get all workflow levels for this change request
            workflows = self.db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.change_request_id == change_request_id
            ).all()
            
            # Check if all levels are approved
            return all(workflow.status == "approved" for workflow in workflows)
            
        except Exception as e:
            logger.error(f"Failed to check approval status: {e}")
            return False
    
    async def _mark_change_request_approved(self, change_request_id: int):
        """Mark change request as approved when all levels are approved"""
        try:
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.id == change_request_id
            ).first()
            
            if change_request:
                change_request.status = "approved"
                change_request.approved_at = datetime.utcnow()
                change_request.updated_at = datetime.utcnow()
                
                self.db.commit()
                
                # Send notification that change request is fully approved
                await self.notification_service.notify_change_request_fully_approved(change_request)
                
                logger.info(f"Change request {change_request.request_id} fully approved")
                
        except Exception as e:
            logger.error(f"Failed to mark change request as approved: {e}")
    
    async def implement_change_request(self, request_id: str, implementer_id: int):
        """Implement an approved change request"""
        try:
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.request_id == request_id
            ).first()
            
            if not change_request:
                raise HTTPException(status_code=404, detail="Change request not found")
            
            if change_request.status != "approved":
                raise HTTPException(status_code=400, detail="Change request is not approved")
            
            # Check if scheduled date is in the future
            if change_request.scheduled_date and change_request.scheduled_date > datetime.utcnow():
                raise HTTPException(
                    status_code=400, 
                    detail=f"Change request is scheduled for {change_request.scheduled_date}"
                )
            
            # Mark as implementing
            change_request.status = "implementing"
            change_request.updated_at = datetime.utcnow()
            self.db.commit()
            
            # TODO: Implement actual changes here
            # This would involve calling the appropriate ACS service methods
            
            # Mark as implemented
            change_request.status = "implemented"
            change_request.implemented_at = datetime.utcnow()
            change_request.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Send success notification
            await self.notification_service.notify_change_implemented(change_request)
            
            logger.info(f"Implemented change request {request_id} by user {implementer_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            # Mark as failed
            if change_request:
                change_request.status = "failed"
                change_request.updated_at = datetime.utcnow()
                self.db.commit()
            
            logger.error(f"Failed to implement change request {request_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to implement change request")
    
    async def get_pending_approvals(self, user_id: int, role: str = None) -> List[ApprovalWorkflow]:
        """Get pending approvals for a user"""
        try:
            query = self.db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.status == "pending"
            )
            
            if role:
                query = query.filter(ApprovalWorkflow.approver_role == role)
            
            # Get change request details
            approvals = query.all()
            
            # Add change request information
            for approval in approvals:
                approval.change_request = self.db.query(ChangeRequest).filter(
                    ChangeRequest.id == approval.change_request_id
                ).first()
            
            return approvals
            
        except Exception as e:
            logger.error(f"Failed to get pending approvals: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve pending approvals")
    
    async def get_change_request_workflow(self, request_id: str) -> List[ApprovalWorkflow]:
        """Get complete workflow for a change request"""
        try:
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.request_id == request_id
            ).first()
            
            if not change_request:
                raise HTTPException(status_code=404, detail="Change request not found")
            
            workflows = self.db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.change_request_id == change_request.id
            ).order_by(ApprovalWorkflow.level).all()
            
            return workflows
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get workflow for change request {request_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve workflow")
    
    async def update_change_request(self, request_id: str, data: Dict[str, Any], user_id: int) -> ChangeRequest:
        """Update change request (only allowed in draft status)"""
        try:
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.request_id == request_id
            ).first()
            
            if not change_request:
                raise HTTPException(status_code=404, detail="Change request not found")
            
            if change_request.status != "draft":
                raise HTTPException(
                    status_code=400, 
                    detail="Change request can only be updated in draft status"
                )
            
            if change_request.requester_id != user_id:
                raise HTTPException(
                    status_code=403, 
                    detail="Only the requester can update the change request"
                )
            
            # Update allowed fields
            allowed_fields = ['title', 'description', 'priority', 'proposed_changes', 
                           'risk_assessment', 'implementation_plan', 'rollback_plan', 'scheduled_date']
            
            for field in allowed_fields:
                if field in data:
                    setattr(change_request, field, data[field])
            
            change_request.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(change_request)
            
            logger.info(f"Updated change request {request_id} by user {user_id}")
            return change_request
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update change request {request_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update change request")
    
    async def delete_change_request(self, request_id: str, user_id: int):
        """Delete change request (only allowed in draft status)"""
        try:
            change_request = self.db.query(ChangeRequest).filter(
                ChangeRequest.request_id == request_id
            ).first()
            
            if not change_request:
                raise HTTPException(status_code=404, detail="Change request not found")
            
            if change_request.status != "draft":
                raise HTTPException(
                    status_code=400, 
                    detail="Change request can only be deleted in draft status"
                )
            
            if change_request.requester_id != user_id:
                raise HTTPException(
                    status_code=403, 
                    detail="Only the requester can delete the change request"
                )
            
            # Delete associated workflows first
            workflows = self.db.query(ApprovalWorkflow).filter(
                ApprovalWorkflow.change_request_id == change_request.id
            ).all()
            
            for workflow in workflows:
                self.db.delete(workflow)
            
            # Delete change request
            self.db.delete(change_request)
            self.db.commit()
            
            logger.info(f"Deleted change request {request_id} by user {user_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete change request {request_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete change request")
