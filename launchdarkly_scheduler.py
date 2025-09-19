#!/usr/bin/env python3
"""
LaunchDarkly Feature Flag Scheduler

This script allows you to schedule targeting rules for LaunchDarkly feature flags
using segment keys at specific dates and times in EST timezone.

Environment Variables Required:
- LD_API_KEY: Your LaunchDarkly API key
- LD_PROJECT_KEY: Your LaunchDarkly project key  
- LD_ENVIRONMENT_KEY: Your LaunchDarkly environment key

Usage:
    python launchdarkly_scheduler.py
"""

import os
import sys
import json
import requests
from datetime import datetime
import pytz
from typing import List, Dict, Any, Optional
import argparse
from dotenv import load_dotenv; load_dotenv()

class LaunchDarklyScheduler:
    """LaunchDarkly API scheduler for feature flag targeting rules."""
    
    def __init__(self):
        """Initialize the scheduler with environment variables."""
        self.api_key = os.getenv('LD_API_KEY')
        self.project_key = os.getenv('LD_PROJECT_KEY')
        self.environment_key = os.getenv('LD_ENVIRONMENT_KEY')
        
        if not all([self.api_key, self.project_key, self.environment_key]):
            raise ValueError(
                "Missing required environment variables. Please set:\n"
                "- LD_API_KEY\n"
                "- LD_PROJECT_KEY\n" 
                "- LD_ENVIRONMENT_KEY"
            )
        
        self.base_url = 'https://app.launchdarkly.com/api/v2'
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Test API connection on initialization
        self._test_api_connection()
    
    def _test_api_connection(self) -> bool:
        """Test the API connection and authentication."""
        try:
            # Test with a simple API call to get project info
            url = f'{self.base_url}/projects/{self.project_key}'
            print(f"🔐 Testing API connection to: {url}")
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 401:
                print("❌ Authentication failed!")
                print("   Please verify your LD_API_KEY is correct and has proper permissions.")
                print("   Make sure you're using a Personal Access Token, not an SDK key.")
                return False
            elif response.status_code == 404:
                print(f"❌ Project '{self.project_key}' not found!")
                print("   Please verify your LD_PROJECT_KEY is correct.")
                return False
            elif response.status_code == 200:
                print("✅ API connection successful!")
                return True
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error testing API connection: {e}")
            return False
    
    def est_to_utc(self, est_time_str: str) -> int:
        """
        Convert EST time string to UTC timestamp in milliseconds.
        
        Args:
            est_time_str: Time string in format 'YYYY-MM-DD HH:MM:SS'
            
        Returns:
            UTC timestamp in milliseconds
        """
        try:
            est = pytz.timezone('US/Eastern')
            utc = pytz.utc
            
            # Parse the EST time
            est_time = datetime.strptime(est_time_str, '%Y-%m-%d %H:%M:%S')
            est_time = est.localize(est_time)
            
            # Convert to UTC
            utc_time = est_time.astimezone(utc)
            
            # Return timestamp in milliseconds
            return int(utc_time.timestamp() * 1000)
            
        except ValueError as e:
            raise ValueError(f"Invalid time format. Use 'YYYY-MM-DD HH:MM:SS': {e}")
    
    def get_flag_config(self, flag_key: str) -> Optional[Dict[str, Any]]:
        """
        Get current flag configuration.
        
        Args:
            flag_key: The feature flag key
            
        Returns:
            Flag configuration dict or None if error
        """
        # Use the correct LaunchDarkly API v2 endpoint format
        url = f'{self.base_url}/flags/{self.project_key}/{flag_key}'
        
        try:
            print(f"🔍 Fetching flag config from: {url}")
            print(f"🔍 Headers being sent: {self.headers}")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 401:
                print(f"❌ Authentication failed. Please check your API key and permissions.")
                print(f"   Response: {response.text}")
                return None
            elif response.status_code == 404:
                print(f"❌ Flag '{flag_key}' not found in project '{self.project_key}'")
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching flag {flag_key}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status Code: {e.response.status_code}")
                print(f"   Response: {e.response.text}")
            return None
    
    def create_targeting_rule(self, segment_key: str, variation: int = 0) -> Dict[str, Any]:
        """
        Create a targeting rule for a segment.
        
        Args:
            segment_key: The segment key to target
            variation: The variation index to serve (default: 0)
            
        Returns:
            Targeting rule dict
        """
        return {
            'clauses': [
                {
                    'attribute': 'segmentMatch',
                    'op': 'segmentMatch', 
                    'values': [segment_key]
                }
            ],
            'variation': variation,
            'rollout': None,
            'trackEvents': False
        }
    
    def schedule_targeting_rules(
        self, 
        flag_key: str, 
        segment_keys: List[str], 
        schedule_time_est: str,
        variation: int = 1
    ) -> bool:
        """
        Schedule targeting rules for a feature flag using LaunchDarkly's Scheduled Changes API.
        
        Args:
            flag_key: The feature flag key
            segment_keys: List of segment keys to target
            schedule_time_est: Schedule time in EST format 'YYYY-MM-DD HH:MM:SS'
            variation: The variation number to serve (default: 1, matches LaunchDarkly UI)
            
        Returns:
            True if successful, False otherwise
        """
        print(f"Scheduling targeting rules for flag: {flag_key}")
        
        # Get current flag configuration
        flag_config = self.get_flag_config(flag_key)
        if not flag_config:
            return False
        
        # Convert EST time to UTC timestamp
        try:
            schedule_time_utc = self.est_to_utc(schedule_time_est)
            schedule_datetime = datetime.fromtimestamp(schedule_time_utc/1000, tz=pytz.UTC)
        except ValueError as e:
            print(f"Error parsing schedule time: {e}")
            return False
        
        # Check if the schedule time is in the future
        now_utc = datetime.now(pytz.UTC)
        if schedule_datetime <= now_utc:
            print(f"❌ Schedule time must be in the future!")
            print(f"   Current time (UTC): {now_utc}")
            print(f"   Schedule time (UTC): {schedule_datetime}")
            return False
        
        # Get the actual variation ID from the flag configuration
        variations = flag_config.get('variations', [])
        # Convert 1-based UI index to 0-based array index
        variation_index = variation - 1
        if variation_index < 0 or variation_index >= len(variations):
            print(f"❌ Variation {variation} is out of range. Flag has {len(variations)} variations (1-{len(variations)}).")
            return False
        
        variation_id = variations[variation_index]['_id']
        print(f"🎯 Using variation ID: {variation_id} (variation {variation})")
        
        # Use LaunchDarkly's Scheduled Changes API
        url = f'{self.base_url}/projects/{self.project_key}/flags/{flag_key}/environments/{self.environment_key}/scheduled-changes'
        
        # Prepare the scheduled changes payload using semantic patch operations
        # Based on LaunchDarkly API docs, we need to use semantic patch format
        scheduled_changes_payload = {
            'executionDate': schedule_time_utc,
            'instructions': [
                {
                    'kind': 'addRule',
                    'variationId': variation_id,
                    'clauses': [
                        {
                            'op': 'segmentMatch',
                            'values': segment_keys,
                            'contextKind': 'user'
                        }
                    ]
                }
            ],
            'comment': f'Scheduled targeting rules for segments: {", ".join(segment_keys)}'
        }
        
        try:
            print(f"🔧 Sending scheduled changes to: {url}")
            print(f"🔧 Execution date: {schedule_datetime} (UTC)")
            print(f"🔧 Instructions: {json.dumps(scheduled_changes_payload['instructions'], indent=2)}")
            
            response = requests.post(url, headers=self.headers, data=json.dumps(scheduled_changes_payload))
            
            if response.status_code == 201:
                print(f"✅ Successfully scheduled targeting rules for flag: {flag_key}")
                print(f"   Segments: {', '.join(segment_keys)}")
                print(f"   Schedule time (EST): {schedule_time_est}")
                print(f"   Schedule time (UTC): {schedule_datetime}")
                print(f"   Scheduled change ID: {response.json().get('_id', 'unknown')}")
                return True
            elif response.status_code == 400:
                print(f"❌ Bad Request (400) for flag {flag_key}")
                print(f"   Response: {response.text}")
                
                # Check for specific error messages
                try:
                    error_data = response.json()
                    if "unknown segment" in error_data.get("message", ""):
                        print(f"   💡 The segment(s) don't exist in your LaunchDarkly project.")
                        print(f"   💡 Please create the segments first or use existing segment keys.")
                    elif "invalid" in error_data.get("message", ""):
                        print(f"   💡 Check that the segment keys and flag configuration are valid.")
                except:
                    pass
                
                return False
            else:
                print(f"❌ Error scheduling rules for flag {flag_key}: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error scheduling rules for flag {flag_key}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status Code: {e.response.status_code}")
                print(f"   Response: {e.response.text}")
            return False
    
    
    def schedule_multiple_flags(
        self,
        flag_keys: List[str],
        segment_keys: List[str], 
        schedule_time_est: str,
        variation: int = 0
    ) -> Dict[str, bool]:
        """
        Schedule targeting rules for multiple feature flags.
        
        Args:
            flag_keys: List of feature flag keys
            segment_keys: List of segment keys to target
            schedule_time_est: Schedule time in EST format 'YYYY-MM-DD HH:MM:SS'
            variation: The variation index to serve (default: 0)
            
        Returns:
            Dict mapping flag keys to success status
        """
        results = {}
        
        print(f"🚀 Starting to schedule targeting rules for {len(flag_keys)} flags")
        print(f"📅 Schedule time (EST): {schedule_time_est}")
        print(f"🎯 Target segments: {', '.join(segment_keys)}")
        print("-" * 60)
        
        for flag_key in flag_keys:
            success = self.schedule_targeting_rules(
                flag_key, segment_keys, schedule_time_est, variation
            )
            results[flag_key] = success
            print()  # Add spacing between flags
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        print("=" * 60)
        print(f"📊 Summary: {successful}/{total} flags scheduled successfully")
        
        if successful < total:
            print("❌ Failed flags:")
            for flag_key, success in results.items():
                if not success:
                    print(f"   - {flag_key}")
        
        return results
    
    def debug_api_info(self):
        """Debug function to print API configuration info."""
        print("🔧 Debug Information:")
        print(f"   API Key: {self.api_key[:8]}..." if self.api_key else "   API Key: Not set")
        print(f"   Project Key: {self.project_key}")
        print(f"   Environment Key: {self.environment_key}")
        print(f"   Base URL: {self.base_url}")
        print(f"   Headers: {self.headers}")
    
    def test_flag_endpoint(self, flag_key: str):
        """Test the specific flag endpoint that's failing."""
        url = f'{self.base_url}/flags/{self.project_key}/{flag_key}'
        print(f"🧪 Testing flag endpoint: {url}")
        print(f"🧪 Headers: {self.headers}")
        
        try:
            response = requests.get(url, headers=self.headers)
            print(f"🧪 Response Status: {response.status_code}")
            print(f"🧪 Response Headers: {dict(response.headers)}")
            print(f"🧪 Response Text: {response.text[:500]}...")
            return response.status_code == 200
        except Exception as e:
            print(f"🧪 Exception: {e}")
            return False
    
    def list_segments(self):
        """List all segments in the project."""
        url = f'{self.base_url}/segments/{self.project_key}'
        print(f"🔍 Listing segments from: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                segments = response.json()
                print(f"📋 Found {len(segments.get('items', []))} segments:")
                for segment in segments.get('items', []):
                    print(f"   - {segment.get('key', 'unknown')}: {segment.get('name', 'No name')}")
                return segments.get('items', [])
            else:
                print(f"❌ Error listing segments: {response.status_code}")
                print(f"   Response: {response.text}")
                return []
        except Exception as e:
            print(f"❌ Exception listing segments: {e}")
            return []
    
    def create_segment(self, segment_key: str, segment_name: str, description: str = ""):
        """Create a new segment in the project."""
        url = f'{self.base_url}/segments/{self.project_key}'
        segment_data = {
            'key': segment_key,
            'name': segment_name,
            'description': description,
            'tags': []
        }
        
        print(f"🔧 Creating segment: {segment_key}")
        print(f"🔧 Segment data: {json.dumps(segment_data, indent=2)}")
        
        try:
            response = requests.post(url, headers=self.headers, data=json.dumps(segment_data))
            if response.status_code == 201:
                print(f"✅ Successfully created segment: {segment_key}")
                return True
            else:
                print(f"❌ Error creating segment: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Exception creating segment: {e}")
            return False


def main():
    """Main function to run the scheduler."""
    parser = argparse.ArgumentParser(
        description='Schedule LaunchDarkly feature flag targeting rules'
    )
    parser.add_argument(
        '--flags', 
        nargs='+', 
        help='List of feature flag keys to schedule'
    )
    parser.add_argument(
        '--segments',
        nargs='+',
        help='List of segment keys to target'
    )
    parser.add_argument(
        '--schedule-time',
        help='Schedule time in EST format (YYYY-MM-DD HH:MM:SS)'
    )
    parser.add_argument(
        '--variation',
        type=int,
        default=1,
        help='Variation number to serve (default: 1, matches LaunchDarkly UI)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show debug information'
    )
    parser.add_argument(
        '--test-flag',
        help='Test a specific flag endpoint'
    )
    parser.add_argument(
        '--list-segments',
        action='store_true',
        help='List all segments in the project'
    )
    parser.add_argument(
        '--create-segment',
        nargs=2,
        metavar=('KEY', 'NAME'),
        help='Create a new segment (key and name)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize scheduler
        scheduler = LaunchDarklyScheduler()
        
        # Show debug info if requested
        if args.debug:
            scheduler.debug_api_info()
            print()
        
        # Test specific flag if requested
        if args.test_flag:
            print(f"🧪 Testing flag endpoint for: {args.test_flag}")
            success = scheduler.test_flag_endpoint(args.test_flag)
            if success:
                print("✅ Flag endpoint test successful!")
            else:
                print("❌ Flag endpoint test failed!")
            return
        
        # List segments if requested
        if args.list_segments:
            print("📋 Listing all segments in the project:")
            scheduler.list_segments()
            return
        
        # Create segment if requested
        if args.create_segment:
            segment_key, segment_name = args.create_segment
            print(f"🔧 Creating segment: {segment_key}")
            success = scheduler.create_segment(segment_key, segment_name)
            if success:
                print("✅ Segment created successfully!")
            else:
                print("❌ Failed to create segment!")
            return
        
        
        # Get inputs
        if args.flags:
            flag_keys = args.flags
        else:
            print("Enter feature flag keys (one per line, empty line to finish):")
            flag_keys = []
            while True:
                flag_key = input().strip()
                if not flag_key:
                    break
                flag_keys.append(flag_key)
        
        if args.segments:
            segment_keys = args.segments
        else:
            print("Enter segment keys (one per line, empty line to finish):")
            segment_keys = []
            while True:
                segment_key = input().strip()
                if not segment_key:
                    break
                segment_keys.append(segment_key)
        
        if args.schedule_time:
            schedule_time_est = args.schedule_time
        else:
            schedule_time_est = input("Enter schedule time (EST format: YYYY-MM-DD HH:MM:SS): ").strip()
        
        # Validate inputs
        if not flag_keys:
            print("❌ No flag keys provided")
            return
        
        if not segment_keys:
            print("❌ No segment keys provided")
            return
        
        if not schedule_time_est:
            print("❌ No schedule time provided")
            return
        
        # Schedule the rules
        scheduler.schedule_multiple_flags(
            flag_keys, segment_keys, schedule_time_est, args.variation
        )
        
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
