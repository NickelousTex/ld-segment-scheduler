# LaunchDarkly Feature Flag Scheduler

⚠️ **WARNING: This tool is NOT officially supported by LaunchDarkly. Use at your own risk.**

A Python web application that leverages LaunchDarkly's **Scheduled Changes API** to schedule targeting rules for feature flags using segment keys at specific dates and times in EST timezone.

## Features

- **Web UI**: Modern, intuitive web interface with dropdown selections
- **Pagination Support**: Handles large numbers of projects, flags, and segments
- **Multi-Project Support**: Select from all accessible LaunchDarkly projects
- **Real-time Validation**: Immediate feedback on selections and scheduling
- **EST Timezone Support**: Automatic UTC conversion for LaunchDarkly API
- **Multiple Flag Scheduling**: Schedule targeting rules for multiple flags at once
- **Segment Targeting**: Target specific user segments with custom variations
- **Comprehensive Error Handling**: Clear error messages and validation
- **No External Dependencies**: LaunchDarkly handles all scheduling execution

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   ```bash
   # Copy the example file
   cp env.example .env
   
   # Edit .env with your LaunchDarkly API key
   LD_API_KEY=your_launchdarkly_api_key
   ```

   **Note**: You only need to set `LD_API_KEY`. The application will let you select projects and environments through the web interface.

3. **Start the application:**
   ```bash
   python web_ui.py
   ```

4. **Access the web interface:**
   Open your browser to `http://localhost:3001`

## Usage

### Web Interface

The web interface provides an intuitive way to schedule feature flag targeting rules:

1. **Select Project**: Choose from all LaunchDarkly projects you have access to
2. **Select Environment**: Pick the target environment for your scheduled changes
3. **Choose Feature Flags**: Select one or more flags to schedule targeting rules for
4. **Select Segments**: Choose the user segments to target
5. **Set Schedule Time**: Pick when the targeting rules should activate (EST timezone)
6. **Choose Variation**: Select which variation to serve to the targeted segments
7. **Schedule**: Click to create the scheduled changes in LaunchDarkly

### Key Features

- **Project Selection**: Automatically loads all accessible LaunchDarkly projects
- **Environment Selection**: Dynamic loading of environments based on selected project
- **Flag & Segment Loading**: Real-time loading with pagination support for large datasets
- **Time Validation**: Ensures scheduled times are in the future
- **Batch Scheduling**: Schedule multiple flags with the same targeting rules
- **Results Display**: Clear feedback on successful and failed scheduling attempts

## Example

### Product Launch Scenario
1. Select your production project and environment
2. Choose multiple feature flags (e.g., "new-checkout-flow", "premium-features")
3. Select target segments (e.g., "premium-users", "beta-testers")
4. Set schedule time for launch (e.g., "2024-02-01 09:00:00 EST")
5. Choose appropriate variations for each flag
6. Schedule all changes at once
## Timezone Handling

The application automatically converts EST times to UTC for LaunchDarkly's API. All schedule times are provided in EST format through the web interface datetime picker.

## Error Handling

The application includes comprehensive error handling for:
- Missing or invalid API keys
- Network connectivity issues
- Invalid project/environment selections
- Missing or invalid flag/segment keys
- Scheduling time validation (must be in the future)
- API rate limiting and timeouts

## Requirements

- Python 3.7+
- requests>=2.31.0
- pytz>=2023.3
- python-dotenv>=1.0.0
- flask>=2.3.0

## Security Considerations

⚠️ **Important Security Notes:**

- This tool requires a LaunchDarkly API key with full project access
- Store your API key securely and never commit it to version control
- The tool creates scheduled changes in LaunchDarkly that will execute automatically
- Review all scheduled changes in the LaunchDarkly dashboard before execution
- Use appropriate API key permissions and rotate keys regularly

## Troubleshooting

### Common Issues

**"Configuration error: Missing LD_API_KEY"**
- Ensure your `.env` file contains a valid `LD_API_KEY`
- Verify the API key has appropriate permissions

**"Error loading projects"**
- Check your internet connection
- Verify your API key is valid and not expired
- Ensure you have access to LaunchDarkly projects

**"No flags/segments available"**
- Verify you've selected a valid project and environment
- Check that the environment contains flags and segments
- Ensure your API key has read permissions for the selected project

**"Schedule time must be in the future"**
- Set a schedule time that is at least a few minutes in the future
- Check that your system clock is accurate

## License

MIT License

## Disclaimer

This tool is not officially supported by LaunchDarkly. Use at your own risk. Always test in non-production environments first and review scheduled changes before they execute.
