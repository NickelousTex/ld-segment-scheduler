#!/usr/bin/env python3
"""
LaunchDarkly Feature Flag Scheduler - Web UI
A lightweight Flask web interface for scheduling feature flag targeting rules.
"""

import os
import json
import requests
import pytz
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

class LaunchDarklyAPI:
    def __init__(self):
        self.api_key = os.getenv('LD_API_KEY')
        self.project_key = os.getenv('LD_PROJECT_KEY')
        self.environment_key = os.getenv('LD_ENVIRONMENT_KEY')
        self.base_url = 'https://app.launchdarkly.com/api/v2'
        
        if not all([self.api_key, self.project_key, self.environment_key]):
            raise ValueError("Missing required environment variables: LD_API_KEY, LD_PROJECT_KEY, LD_ENVIRONMENT_KEY")
        
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def get_flags(self):
        """Get all feature flags in the project with pagination."""
        all_flags = []
        offset = 0
        limit = 20
        
        while True:
            url = f'{self.base_url}/flags/{self.project_key}?limit={limit}&offset={offset}'
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    flags = data.get('items', [])
                    
                    if not flags:  # No more flags
                        break
                    
                    all_flags.extend([{
                        'key': flag['key'], 
                        'name': flag.get('name', flag['key']),
                        'creationDate': flag.get('creationDate', 0)
                    } for flag in flags])
                    
                    # Check if we got fewer than the limit (last page)
                    if len(flags) < limit:
                        break
                    
                    offset += limit
                else:
                    print(f"Error fetching flags: {response.status_code}")
                    break
            except Exception as e:
                print(f"Error fetching flags: {e}")
                break
        
        # Sort flags by creation date (newest first)
        all_flags.sort(key=lambda x: x.get('creationDate', 0), reverse=True)
        return all_flags
    
    def get_segments(self):
        """Get all segments in the environment with pagination."""
        all_segments = []
        offset = 0
        limit = 20
        
        while True:
            url = f'{self.base_url}/segments/{self.project_key}/{self.environment_key}?limit={limit}&offset={offset}'
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    segments = data.get('items', [])
                    
                    if not segments:  # No more segments
                        break
                    
                    all_segments.extend([{
                        'key': segment['key'], 
                        'name': segment.get('name', segment['key']),
                        'creationDate': segment.get('creationDate', 0)
                    } for segment in segments])
                    
                    # Check if we got fewer than the limit (last page)
                    if len(segments) < limit:
                        break
                    
                    offset += limit
                else:
                    print(f"Error fetching segments: {response.status_code}")
                    break
            except Exception as e:
                print(f"Error fetching segments: {e}")
                break
        
        # Sort segments by creation date (newest first)
        all_segments.sort(key=lambda x: x.get('creationDate', 0), reverse=True)
        return all_segments
    
    def get_flag_config(self, flag_key):
        """Get flag configuration."""
        url = f'{self.base_url}/flags/{self.project_key}/{flag_key}'
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching flag config: {e}")
            return None
    
    def est_to_utc(self, est_time_str):
        """Convert EST time string to UTC timestamp."""
        try:
            # Handle both formats: ISO format from datetime-local input and CLI format
            if 'T' in est_time_str:
                # ISO format from datetime-local input (e.g., "2025-10-16T23:50")
                est_time = datetime.fromisoformat(est_time_str)
            else:
                # CLI format (e.g., "2025-10-16 23:50:00")
                est_time = datetime.strptime(est_time_str, '%Y-%m-%d %H:%M:%S')
            
            # Set timezone to EST
            est_tz = pytz.timezone('US/Eastern')
            est_time = est_tz.localize(est_time)
            
            # Convert to UTC
            utc_time = est_time.astimezone(pytz.UTC)
            
            # Return timestamp in milliseconds
            return int(utc_time.timestamp() * 1000)
        except ValueError as e:
            raise ValueError(f"Invalid time format: {e}")
    
    def schedule_targeting_rules(self, flag_key, segment_keys, schedule_time_est, variation=1):
        """Schedule targeting rules for a feature flag."""
        # Get current flag configuration
        flag_config = self.get_flag_config(flag_key)
        if not flag_config:
            return False, "Failed to fetch flag configuration"
        
        # Convert EST time to UTC timestamp
        try:
            schedule_time_utc = self.est_to_utc(schedule_time_est)
            schedule_datetime = datetime.fromtimestamp(schedule_time_utc/1000, tz=pytz.UTC)
        except ValueError as e:
            return False, f"Error parsing schedule time: {e}"
        
        # Check if the schedule time is in the future
        now_utc = datetime.now(pytz.UTC)
        if schedule_datetime <= now_utc:
            return False, "Schedule time must be in the future!"
        
        # Get the actual variation ID from the flag configuration
        variations = flag_config.get('variations', [])
        # Convert 1-based UI index to 0-based array index
        variation_index = variation - 1
        if variation_index < 0 or variation_index >= len(variations):
            return False, f"Variation {variation} is out of range. Flag has {len(variations)} variations (1-{len(variations)})."
        
        variation_id = variations[variation_index]['_id']
        
        # Use LaunchDarkly's Scheduled Changes API
        url = f'{self.base_url}/projects/{self.project_key}/flags/{flag_key}/environments/{self.environment_key}/scheduled-changes'
        
        # Prepare the scheduled changes payload
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
            response = requests.post(url, headers=self.headers, data=json.dumps(scheduled_changes_payload))
            
            if response.status_code == 201:
                scheduled_change_id = response.json().get('_id', 'unknown')
                return True, f"Successfully scheduled targeting rules! Scheduled change ID: {scheduled_change_id}"
            elif response.status_code == 400:
                error_data = response.json()
                error_msg = error_data.get("message", "Bad Request")
                if "unknown segment" in error_msg:
                    return False, "One or more segments don't exist in your LaunchDarkly project."
                else:
                    return False, f"Bad Request: {error_msg}"
            else:
                return False, f"Error scheduling rules: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Error scheduling rules: {e}"

# Initialize the API client
try:
    ld_api = LaunchDarklyAPI()
except ValueError as e:
    print(f"Configuration error: {e}")
    ld_api = None

@app.route('/')
def index():
    """Main page with the scheduling form."""
    if ld_api is None:
        return render_template('error.html', error="Configuration error: Missing environment variables")
    
    try:
        print("🔄 Loading flags and segments...")
        flags = ld_api.get_flags()
        segments = ld_api.get_segments()
        print(f"✅ Loaded {len(flags)} flags and {len(segments)} segments")
        return render_template('index.html', flags=flags, segments=segments)
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return render_template('error.html', error=f"Error loading data: {e}")

@app.route('/api/flags')
def api_flags():
    """API endpoint to get flags."""
    if ld_api is None:
        return jsonify({'error': 'Configuration error'}), 500
    
    try:
        flags = ld_api.get_flags()
        return jsonify(flags)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/segments')
def api_segments():
    """API endpoint to get segments."""
    if ld_api is None:
        return jsonify({'error': 'Configuration error'}), 500
    
    try:
        segments = ld_api.get_segments()
        return jsonify(segments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/schedule', methods=['POST'])
def schedule():
    """Handle the scheduling form submission."""
    if ld_api is None:
        flash('Configuration error: Missing environment variables', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get form data
        flag_keys = request.form.getlist('flags')
        segment_keys = request.form.getlist('segments')
        schedule_time = request.form.get('schedule_time')
        variation = int(request.form.get('variation', 1))
        
        if not flag_keys:
            flash('Please select at least one flag', 'error')
            return redirect(url_for('index'))
        
        if not segment_keys:
            flash('Please select at least one segment', 'error')
            return redirect(url_for('index'))
        
        if not schedule_time:
            flash('Please enter a schedule time', 'error')
            return redirect(url_for('index'))
        
        # Schedule for each flag
        results = []
        for flag_key in flag_keys:
            success, message = ld_api.schedule_targeting_rules(
                flag_key, segment_keys, schedule_time, variation
            )
            results.append({'flag': flag_key, 'success': success, 'message': message})
        
        # Show results
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        if success_count == total_count:
            flash(f'Successfully scheduled {success_count}/{total_count} flags!', 'success')
        else:
            flash(f'Scheduled {success_count}/{total_count} flags. Check details below.', 'warning')
        
        # Store results for display (using session)
        from flask import session
        session['results'] = results
        
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error: {e}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3001)
