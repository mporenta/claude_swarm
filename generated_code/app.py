"""
Flask application that displays 'Hello World' with random styling.

This application generates random text color, font size, and font family
on each page refresh and passes these values to the template.
"""

import random
from typing import Tuple
from flask import Flask, render_template

app = Flask(__name__)


def generate_random_styles() -> Tuple[str, int, str]:
    """
    Generate random styling values for text display.

    Returns:
        Tuple[str, int, str]: A tuple containing:
            - color (str): Random text color
            - font_size (int): Random font size in pixels
            - font_family (str): Random font family name
    """
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'teal',
              'magenta', 'gold']
    font_families = ['Arial', 'Helvetica', 'Georgia', 'Times New Roman',
                     'Courier', 'Verdana']

    color = random.choice(colors)
    font_size = random.randint(20, 100)
    font_family = random.choice(font_families)

    return color, font_size, font_family


@app.route('/')
def index() -> str:
    """
    Render the homepage with randomly generated styling values.

    Returns:
        str: Rendered HTML template with random styling applied

    Raises:
        Exception: Any rendering errors are caught and logged
    """
    try:
        color, font_size, font_family = generate_random_styles()
        return render_template(
            'index.html',
            color=color,
            font_size=font_size,
            font_family=font_family
        )
    except Exception as e:
        app.logger.error(f"Error rendering template: {e}")
        return "An error occurred while loading the page.", 500


@app.errorhandler(404)
def page_not_found(e) -> Tuple[str, int]:
    """
    Handle 404 errors.

    Args:
        e: The error object

    Returns:
        Tuple[str, int]: Error message and status code
    """
    return "Page not found.", 404


@app.errorhandler(500)
def internal_server_error(e) -> Tuple[str, int]:
    """
    Handle 500 errors.

    Args:
        e: The error object

    Returns:
        Tuple[str, int]: Error message and status code
    """
    app.logger.error(f"Internal server error: {e}")
    return "Internal server error.", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)
