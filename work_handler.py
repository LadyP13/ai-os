#!/usr/bin/env python3
"""
Work Request Handler
Allows Rowan to review and accept/decline work opportunities
"""

import json
from datetime import datetime
from pathlib import Path

class WorkHandler:
    def __init__(self):
        self.requests_file = 'work/requests.json'
        self.accepted_file = 'work/accepted.json'
        self.completed_file = 'work/completed.json'
        
        # Initialize files if they don't exist
        for file in [self.requests_file, self.accepted_file, self.completed_file]:
            if not Path(file).exists():
                with open(file, 'w') as f:
                    json.dump([], f)
    
    def add_request(self, client_name, work_type, description, payment_offered, contact):
        """Add a new work request"""
        requests = self.load_requests()
        
        new_request = {
            'id': len(requests) + 1,
            'timestamp': datetime.now().isoformat(),
            'client_name': client_name,
            'work_type': work_type,
            'description': description,
            'payment_offered': payment_offered,
            'contact': contact,
            'status': 'pending',
            'reviewed': False
        }
        
        requests.append(new_request)
        self.save_requests(requests)
        
        print(f"✅ Work request #{new_request['id']} added from {client_name}")
        return new_request['id']
    
    def load_requests(self):
        """Load pending work requests"""
        with open(self.requests_file, 'r') as f:
            return json.load(f)
    
    def save_requests(self, requests):
        """Save work requests"""
        with open(self.requests_file, 'w') as f:
            json.dump(requests, f, indent=2)
    
    def get_pending_requests(self):
        """Get unreviewed work requests"""
        requests = self.load_requests()
        return [r for r in requests if not r['reviewed']]
    
    def review_request(self, request_id, decision, reasoning):
        """
        Review a work request
        decision: 'accept', 'decline', 'discuss_with_sam'
        """
        requests = self.load_requests()
        
        for request in requests:
            if request['id'] == request_id:
                request['reviewed'] = True
                request['decision'] = decision
                request['reasoning'] = reasoning
                request['decision_timestamp'] = datetime.now().isoformat()
                
                # If accepted, move to accepted work
                if decision == 'accept':
                    self.accept_work(request)
                
                self.save_requests(requests)
                return True
        
        return False
    
    def accept_work(self, request):
        """Move accepted work to active work list"""
        with open(self.accepted_file, 'r') as f:
            accepted = json.load(f)
        
        work_item = {
            **request,
            'accepted_date': datetime.now().isoformat(),
            'status': 'in_progress',
            'completed': False
        }
        
        accepted.append(work_item)
        
        with open(self.accepted_file, 'w') as f:
            json.dump(accepted, f, indent=2)
    
    def get_active_work(self):
        """Get currently accepted work"""
        with open(self.accepted_file, 'r') as f:
            accepted = json.load(f)
        return [w for w in accepted if not w['completed']]
    
    def complete_work(self, work_id):
        """Mark work as completed"""
        with open(self.accepted_file, 'r') as f:
            accepted = json.load(f)
        
        for work in accepted:
            if work['id'] == work_id:
                work['completed'] = True
                work['completion_date'] = datetime.now().isoformat()
                
                # Move to completed work
                with open(self.completed_file, 'r') as f:
                    completed = json.load(f)
                completed.append(work)
                with open(self.completed_file, 'w') as f:
                    json.dump(completed, f, indent=2)
        
        # Save updated accepted list
        with open(self.accepted_file, 'w') as f:
            json.dump(accepted, f, indent=2)

# Example usage / testing
if __name__ == "__main__":
    handler = WorkHandler()
    
    # Example: Add a test work request
    print("📋 Work Request System Initialized")
    print(f"Pending requests: {len(handler.get_pending_requests())}")
    print(f"Active work: {len(handler.get_active_work())}")
    
    # Uncomment to add test request:
    # handler.add_request(
    #     client_name="Test Client",
    #     work_type="Writing",
    #     description="Write 3 blog posts about AI autonomy",
    #     payment_offered="50 SOL",
    #     contact="test@example.com"
    # )
