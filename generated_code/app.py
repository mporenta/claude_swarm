"""
Flask Hello World Application.

A simple Flask web application that displays 'Hello World'
with randomized styling on each page refresh.
"""

from flask import Flask, render_template
import random


app = Flask(__name__)

# Constants for random value generation
COLORS = [
    'red', 'blue', 'green', 'purple',
    'orange', 'teal', 'magenta', 'gold'
]
FONTS = [
    'Arial', 'Helvetica', 'Georgia',
    'Times New Roman', 'Courier', 'Verdana'
]
MIN_FONT_SIZE = 20
MAX_FONT_SIZE = 100


@app.route('/')
def index():
    """
    Render the homepage with randomized styling.

    Generates random color, font size, and font family values
    and passes them to the index.html template.

    Returns:
        str: Rendered HTML template with dynamic styling.
    """
    try:
        # Generate random styling values
        color = random.choice(COLORS)
        font_size_num = random.randint(MIN_FONT_SIZE, MAX_FONT_SIZE)
        font_size = f"{font_size_num}px"
        font_family = random.choice(FONTS)

        # Render template with random values
        return render_template(
            'index.html',
            color=color,
            font_size=font_size,
            font_family=font_family
        )
    except Exception as e:
        # Return error response if template rendering fails
        return f"Internal Server Error: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5010, debug=False)
