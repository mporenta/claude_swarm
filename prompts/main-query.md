# Flask Hello World Project

## Project Overview
This is a Flask web application that displays "Hello World" with randomized styling on each page refresh.

## Requirements
- Flask web framework
- Python 3.8+
- Random styling on each refresh (color, size, font)
- Run on port 5010
- Clean, modern HTML/CSS

## Project Structure
```
flask_app/
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # Homepage template
└── requirements.txt    # Python dependencies
```

## Key Guidelines
1. **Code Quality**
   - Follow PEP 8 style guidelines
   - Include proper error handling
   - Add clear docstrings
   - Use Flask best practices
   - Run project files through flake8 to ensure code quality

2. **Security**
   - Never expose debug mode in production
   - Validate all user inputs
   - Use secure headers

3. **Testing**
   - Test the random styling functionality
   - Verify the app runs on correct port
   - Check template rendering
   - Run project files through flake8 to ensure code quality

## Implementation Notes
- Use Python's `random` module for styling variations
- Pass styling variables from Flask to template
- Keep the design simple and responsive
- Ensure cross-browser compatibility

## Development Workflow
1. Create Flask app structure
2. Implement random styling logic
3. Create HTML template with dynamic styles
4. Test locally on port 5010
5. Run project files through flake8 to ensure code quality
6. Review code for quality and security

## Tools Allowed
- Read, Write, Edit files
- Bash for testing and running the server
- Grep for searching code patterns


**Follow the guidelines in CLAUDE.md. Create professional, production-ready code.**