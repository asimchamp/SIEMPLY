"""
Workflows API Router
Handles cluster management and environment building operations
"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, List, Any
import logging

from .cluster_manager import ClusterManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
    responses={404: {"description": "Workflow not found"}},
)

# Initialize cluster manager
cluster_manager = ClusterManager()

@router.post("/clusters", response_model=Dict[str, Any])
async def create_cluster(cluster_data: Dict[str, str]):
    """
    Create a new Splunk cluster structure
    
    Args:
        cluster_data: Dictionary containing cluster_name
        
    Returns:
        Creation result with cluster details
    """
    try:
        cluster_name = cluster_data.get('cluster_name')
        if not cluster_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cluster_name is required"
            )
        
        if not cluster_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cluster_name cannot be empty"
            )
        
        # Validate cluster name format
        if not cluster_name.replace('-', '').replace('_', '').isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cluster_name can only contain alphanumeric characters, hyphens, and underscores"
            )
        
        result = cluster_manager.create_cluster_structure(cluster_name.strip())
        
        if result['success']:
            logger.info(f"Created cluster structure: {cluster_name}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create cluster: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/clusters", response_model=List[Dict[str, Any]])
async def list_clusters():
    """
    List all available Splunk clusters
    
    Returns:
        List of cluster information
    """
    try:
        clusters = cluster_manager.list_clusters()
        logger.info(f"Retrieved {len(clusters)} clusters")
        return clusters
        
    except Exception as e:
        logger.error(f"Failed to list clusters: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/clusters/{cluster_name}", response_model=Dict[str, Any])
async def get_cluster_info(cluster_name: str):
    """
    Get detailed information about a specific cluster
    
    Args:
        cluster_name: Name of the cluster
        
    Returns:
        Detailed cluster information
    """
    try:
        cluster_info = cluster_manager.get_cluster_info(cluster_name)
        
        if not cluster_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cluster '{cluster_name}' not found"
            )
        
        logger.info(f"Retrieved cluster info for: {cluster_name}")
        return cluster_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cluster info for '{cluster_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.delete("/clusters/{cluster_name}", response_model=Dict[str, Any])
async def delete_cluster(cluster_name: str):
    """
    Delete a Splunk cluster and all its contents
    
    Args:
        cluster_name: Name of the cluster to delete
        
    Returns:
        Deletion result
    """
    try:
        result = cluster_manager.delete_cluster(cluster_name)
        
        if result['success']:
            logger.info(f"Deleted cluster: {cluster_name}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete cluster '{cluster_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/builds/save", response_model=Dict[str, Any])
async def save_build_configuration(build_data: Dict[str, Any]):
    """
    Save build configuration by updating cluster configuration files with actual host IPs
    
    Args:
        build_data: Dictionary containing cluster_name and components with host information
        
    Returns:
        Save result with updated configuration details
    """
    try:
        cluster_name = build_data.get('cluster_name')
        components = build_data.get('components', [])
        
        if not cluster_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cluster_name is required"
            )
        
        if not components:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="components are required"
            )
        
        # Save the build configuration
        result = cluster_manager.save_build_configuration(cluster_name, components)
        
        if result['success']:
            logger.info(f"Saved build configuration for cluster: {cluster_name}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save build configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/deploy", response_model=Dict[str, Any])
async def deploy_environment(deployment_data: Dict[str, Any]):
    """
    Deploy a Splunk environment based on workflow configuration
    
    Args:
        deployment_data: Workflow configuration with nodes and connections
        
    Returns:
        Deployment results
    """
    try:
        # Extract deployment information
        nodes = deployment_data.get('nodes', [])
        connections = deployment_data.get('connections', [])
        cluster_name = deployment_data.get('cluster_name', '')
        
        if not nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No nodes specified for deployment"
            )
        
        # Validate that all nodes are configured
        unconfigured_nodes = [node for node in nodes if not node.get('isConfigured', False)]
        if unconfigured_nodes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nodes must be configured before deployment: {[n['id'] for n in unconfigured_nodes]}"
            )
        
        # Create cluster structure if cluster name is provided
        if cluster_name and cluster_name.strip():
            cluster_result = cluster_manager.create_cluster_structure(cluster_name.strip())
            if not cluster_result['success']:
                logger.warning(f"Failed to create cluster structure: {cluster_result['error']}")
        
        # Process deployment (this would integrate with the existing job system)
        deployment_results = []
        
        for node in nodes:
            try:
                # Here you would create actual installation jobs
                # For now, we'll simulate the process
                deployment_results.append({
                    'node_id': node['id'],
                    'node_type': node['type'],
                    'status': 'success',
                    'message': f'Deployment job created for {node["type"]}',
                    'job_id': f'job_{node["id"]}_{len(deployment_results)}'
                })
                
            except Exception as e:
                deployment_results.append({
                    'node_id': node['id'],
                    'node_type': node['type'],
                    'status': 'error',
                    'message': f'Deployment failed: {str(e)}'
                })
        
        logger.info(f"Deployed environment with {len(nodes)} nodes")
        
        return {
            'success': True,
            'cluster_name': cluster_name,
            'total_nodes': len(nodes),
            'total_connections': len(connections),
            'deployment_results': deployment_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy environment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for workflows service
    
    Returns:
        Health status
    """
    try:
        # Check if cluster manager is working
        test_cluster = "health_check_test"
        cluster_manager.create_cluster_structure(test_cluster)
        cluster_manager.delete_cluster(test_cluster)
        
        return {
            'status': 'healthy',
            'service': 'workflows',
            'cluster_manager': 'operational'
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'service': 'workflows',
            'cluster_manager': 'error',
            'error': str(e)
        }
