# LaunchDarkly Feature Flag Scheduler

A Python script that leverages LaunchDarkly's native **Scheduled Changes API** to schedule targeting rules for feature flags using segment keys at specific dates and times in EST timezone.

## Features

- **Native LaunchDarkly Scheduling**: Uses LaunchDarkly's built-in Scheduled Changes API
- **Web UI**: Modern web interface with dropdown selections for flags and segments
- **Command Line Interface**: Full CLI support for automation and scripting
- Schedule targeting rules for multiple feature flags
- Target specific segments with custom variations
- EST timezone support with automatic UTC conversion
- Pagination support for large numbers of flags and segments
- Comprehensive error handling and validation
- No external dependencies for scheduling (LaunchDarkly handles execution)

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   # Copy the example file
   cp env.example .env
   
   # Edit .env with your actual values
   LD_API_KEY=your_actual_api_key
   LD_PROJECT_KEY=your_actual_project_key
   LD_ENVIRONMENT_KEY=your_actual_environment_key
   ```

3. **Load environment variables:**
   ```bash
   # Option 1: Use python-dotenv (recommended)
   pip install python-dotenv
   # Then add to your script: from dotenv import load_dotenv; load_dotenv()
   
   # Option 2: Export manually
   export LD_API_KEY=your_api_key
   export LD_PROJECT_KEY=your_project_key
   export LD_ENVIRONMENT_KEY=your_environment_key
   ```

## Usage

### Web UI (Recommended)
Start the web interface for easy scheduling:

```bash
# Set environment variables
export LD_API_KEY=your_api_key
export LD_PROJECT_KEY=your_project_key
export LD_ENVIRONMENT_KEY=your_environment_key

# Start the web UI
python web_ui.py
```

Then open your browser to `http://localhost:3001` and use the intuitive web interface with:
- Dropdown selections for flags and segments
- Visual count of available items
- Date/time picker for scheduling
- Real-time feedback and results

### Command Line Interface
```bash
python launchdarkly_scheduler.py \
  --flags flag-key-1 flag-key-2 \
  --segments segment-key-1 segment-key-2 \
  --schedule-time "2024-01-15 14:30:00" \
  --variation 0
```

### Interactive Mode
```bash
python launchdarkly_scheduler.py
```

### Parameters

- `--flags`: List of feature flag keys to schedule
- `--segments`: List of segment keys to target
- `--schedule-time`: Schedule time in EST format (YYYY-MM-DD HH:MM:SS)
- `--variation`: Variation number to serve (default: 1, matches LaunchDarkly UI)

## Examples

### Schedule multiple flags for a product launch
```bash
python launchdarkly_scheduler.py \
  --flags new-checkout-flow premium-features beta-dashboard \
  --segments premium-users beta-testers \
  --schedule-time "2024-02-01 09:00:00"
```

### Schedule a single flag with custom variation
```bash
python launchdarkly_scheduler.py \
  --flags special-promotion \
  --segments vip-customers \
  --schedule-time "2024-01-20 12:00:00" \
  --variation 1
```

### Create segments and schedule rules
```bash
# First create a segment
python launchdarkly_scheduler.py --create-segment premium-users "Premium Users"

# Then schedule rules using that segment
python launchdarkly_scheduler.py \
  --flags new-feature \
  --segments premium-users \
  --schedule-time "2024-12-25 10:00:00"
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `LD_API_KEY` | LaunchDarkly API key | `api-1234567890abcdef` |
| `LD_PROJECT_KEY` | LaunchDarkly project key | `my-project` |
| `LD_ENVIRONMENT_KEY` | LaunchDarkly environment key | `production` |

## Timezone Handling

The script automatically converts EST times to UTC for LaunchDarkly's API. All schedule times should be provided in EST format: `YYYY-MM-DD HH:MM:SS`.

## Error Handling

The script includes comprehensive error handling for:
- Missing environment variables
- Invalid time formats
- API connection issues
- Invalid flag or segment keys
- Network timeouts

## Requirements

- Python 3.7+
- requests>=2.31.0
- pytz>=2023.3
- python-dotenv>=1.0.0
- flask>=2.3.0 (for web UI)

## License

MIT License
