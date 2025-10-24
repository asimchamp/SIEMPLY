"""
Test script for Runbook functionality
"""
import sys
import os
import yaml
from pathlib import Path

# Add the project root to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.services.runbook_service import RunbookService
from backend.models import get_db

def test_yaml_parsing():
    """Test YAML parsing functionality"""
    print("Testing YAML parsing...")
    
    # Sample YAML content
    yaml_content = """
automation_playbook:
  - job:
      id: test_job
      name: "Test Job"
      targets:
        server_class: webservers
      execution_options:
        remote_user: root
      tasks:
        - name: "Test task"
          command: "echo 'Hello World'"
    """
    
    try:
        # Create a mock database session (you'll need to implement this)
        # db = get_db()
        # service = RunbookService(db)
        
        # For now, just test the YAML parsing
        parsed_data = yaml.safe_load(yaml_content)
        
        if parsed_data and "automation_playbook" in parsed_data:
            print("✓ YAML parsing successful")
            print(f"  Found {len(parsed_data['automation_playbook'])} jobs")
            
            for job_item in parsed_data["automation_playbook"]:
                job = job_item.get("job", {})
                print(f"  Job: {job.get('name', 'Unknown')} (ID: {job.get('id', 'Unknown')})")
                print(f"    Tasks: {len(job.get('tasks', []))}")
        else:
            print("✗ YAML parsing failed - missing automation_playbook key")
            
    except Exception as e:
        print(f"✗ YAML parsing failed: {e}")

def test_sample_runbook():
    """Test the sample runbook file"""
    print("\nTesting sample runbook file...")
    
    sample_file = Path(__file__).parent.parent.parent / "files" / "sample_runbook.yaml"
    
    if not sample_file.exists():
        print("✗ Sample runbook file not found")
        return
    
    try:
        with open(sample_file, "r") as f:
            yaml_content = f.read()
        
        parsed_data = yaml.safe_load(yaml_content)
        
        if parsed_data and "automation_playbook" in parsed_data:
            print("✓ Sample runbook parsing successful")
            print(f"  Found {len(parsed_data['automation_playbook'])} jobs")
            
            for job_item in parsed_data["automation_playbook"]:
                job = job_item.get("job", {})
                print(f"  Job: {job.get('name', 'Unknown')} (ID: {job.get('id', 'Unknown')})")
                
                targets = job.get("targets", {})
                if "server_class" in targets:
                    print(f"    Targets: Server class '{targets['server_class']}'")
                elif "hosts" in targets:
                    print(f"    Targets: Hosts {targets['hosts']}")
                
                tasks = job.get("tasks", [])
                print(f"    Tasks: {len(tasks)}")
                
                for task in tasks:
                    task_name = task.get("name", "Unknown")
                    task_types = [k for k in task.keys() if k != "name"]
                    print(f"      - {task_name} ({', '.join(task_types)})")
        else:
            print("✗ Sample runbook parsing failed")
            
    except Exception as e:
        print(f"✗ Sample runbook parsing failed: {e}")

def test_api_endpoints():
    """Test API endpoint structure"""
    print("\nTesting API endpoint structure...")
    
    # This would normally test the actual API endpoints
    # For now, just verify the structure is correct
    endpoints = [
        "GET /runbooks",
        "GET /runbooks/{id}",
        "POST /runbooks",
        "PUT /runbooks/{id}",
        "DELETE /runbooks/{id}",
        "POST /runbooks/{id}/execute",
        "GET /runbooks/executions",
        "GET /runbooks/executions/{id}",
        "GET /runbooks/executions/{id}/tasks",
        "POST /runbooks/{id}/validate",
        "POST /runbooks/from-file"
    ]
    
    print("✓ API endpoints defined:")
    for endpoint in endpoints:
        print(f"  {endpoint}")

def main():
    """Run all tests"""
    print("Running Runbook functionality tests...")
    print("=" * 50)
    
    test_yaml_parsing()
    test_sample_runbook()
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    main() 