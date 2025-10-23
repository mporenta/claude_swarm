"""
Flask application that displays Hello World with randomized styling.

This application serves a single homepage route that generates random
styling attributes (color, font size, font family) on each page refresh.
"""

import random
from typing import Dict, Any
from flask import Flask, render_template

app = Flask(__name__)

# Configuration constants
COLORS = ['red', 'blue', 'green', 'purple', 'orange', 'teal', 'magenta',
          'gold']
FONT_FAMILIES = ['Arial', 'Helvetica', 'Georgia', 'Times New Roman',
                 'Courier', 'Verdana']
MIN_FONT_SIZE = 20
MAX_FONT_SIZE = 100


def generate_random_styles() -> Dict[str, Any]:
    """
    Generate random styling values for the page.

    Returns:
        Dict[str, Any]: Dictionary containing random color, font_size,
                        and font_family values.
    """
    return {
        'color': random.choice(COLORS),
        'font_size': f"{random.randint(MIN_FONT_SIZE, MAX_FONT_SIZE)}px",
        'font_family': random.choice(FONT_FAMILIES)
    }


@app.route('/')
def index() -> str:
    """
    Render the homepage with randomized styling.

    Returns:
        str: Rendered HTML template with random style attributes.
    """
    try:
        styles = generate_random_styles()
        return render_template(
            'index.html',
            color=styles['color'],
            font_size=styles['font_size'],
            font_family=styles['font_family']
        )
    except Exception as e:
        app.logger.error(f"Error rendering template: {str(e)}")
        return "An error occurred while loading the page.", 500


@app.errorhandler(404)
def not_found(error: Any) -> tuple:
    """
    Handle 404 errors.

    Args:
        error: The error object.

    Returns:
        tuple: Error message and status code.
    """
    return "Page not found.", 404


@app.errorhandler(500)
def internal_error(error: Any) -> tuple:
    """
    Handle 500 errors.

    Args:
        error: The error object.

    Returns:
        tuple: Error message and status code.
    """
    app.logger.error(f"Internal server error: {str(error)}")
    return "An internal server error occurred.", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)
