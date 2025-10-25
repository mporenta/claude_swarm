# Flask Hello World Application - Multi-Agent Orchestration

## Project Goal
Create a professional Flask web application that displays "Hello World" with randomized styling on each page refresh. Run on port 5010 with production-ready code quality.

---

## 🚀 Orchestration Workflow

### Step 1: Backend Development
@flask-developer

Create the Flask application backend with the following specifications:

**File**: `flask_app/app.py`

**Requirements**:
1. **Random Styling Functions**:
   - `get_random_color()` - Returns random hex color (#000000-#FFFFFF)
   - `get_random_font_size()` - Returns random size (30-80 pixels)
   - `get_random_font()` - Returns random font from: Arial, Courier New, Georgia, Times New Roman, Verdana, Comic Sans MS, Impact, Trebuchet MS
   - `get_random_background()` - Returns random hex background color

2. **Flask Route**:
   - Single route: `@app.route('/')`
   - Function name: `index()`
   - Pass styling variables to template: `color`, `font_size`, `font_family`, `bg_color`
   - Use: `render_template('index.html', **styles)`

3. **Error Handlers**:
   - `@app.errorhandler(404)` - Return "Page not found", 404
   - `@app.errorhandler(500)` - Return "Internal server error", 500

4. **Production Configuration**:
   - Port: 5010
   - Host: 0.0.0.0
   - Debug: False (production mode)

5. **Code Quality**:
   - PEP 8 compliant formatting
   - Comprehensive docstrings for all functions (Google style)
   - Type hints not required (maintain Python 3.8+ compatibility)
   - Clean, readable code structure

**File**: `flask_app/requirements.txt`

Include:
```
Flask==3.0.0
Werkzeug==3.0.1
click==8.1.7
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.3
```

**Critical**: Verify directory structure before writing files:
- app.py MUST be at: `flask_app/app.py` (NOT in templates/)
- Use `Write` tool with correct full paths

---

### Step 2: Frontend Development
@frontend-developer

Create the HTML template with modern, responsive design.

**File**: `flask_app/templates/index.html`

**Requirements**:
1. **HTML5 Structure**:
   - Proper DOCTYPE, html, head, body tags
   - Meta tags: charset UTF-8, viewport for mobile
   - Title: "Hello World - Flask App"

2. **Dynamic Styling** (Jinja2 variables):
   - Text color: `{{ color }}`
   - Font size: `{{ font_size }}px`
   - Font family: `{{ font_family }}`
   - Background color: `{{ bg_color }}`

3. **Content**:
   - Main heading: `<h1>Hello World!</h1>`
   - Subtext: "Refresh the page to see different styles"

4. **CSS Design**:
   - **Modern Effects**:
     - Glassmorphism card effect (rgba transparency, backdrop-filter blur)
     - CSS animations (fadeIn for h1)
     - Box shadows for depth
     - Smooth transitions
   - **Layout**:
     - Centered content (flexbox: center/center)
     - Min-height: 100vh
     - Proper padding and spacing
   - **Responsive Design**:
     - Mobile breakpoint: @media (max-width: 768px)
     - Scale font size appropriately for mobile
     - Adjust padding for smaller screens
   - **Accessibility**:
     - Semantic HTML5 elements
     - Sufficient color contrast
     - Readable font sizes

5. **Style Organization**:
   - All styles in `<style>` tag in `<head>`
   - Reset CSS: `* { margin: 0; padding: 0; box-sizing: border-box; }`
   - Organized sections: base styles, layout, components, animations, responsive

**Design Goal**: Professional, modern UI that works across all devices

---

### Step 3: Documentation
@flask-developer

Create comprehensive project documentation.

**File**: `flask_app/README.md`

**Sections**:
1. **Project Title & Description**
2. **Features List** (random color, font, size, background)
3. **Project Structure** (tree view of files)
4. **Installation Instructions**:
   - Virtual environment setup
   - Dependencies installation
5. **Running the Application**:
   - Start command: `python app.py`
   - Access URL: `http://localhost:5010`
6. **Configuration** (port, host, debug mode)
7. **Styling Features** (detailed explanation)
8. **Code Quality** (PEP 8, docstrings, error handling)
9. **Security Features** (debug=False, error handlers)
10. **Browser Compatibility** (Chrome, Firefox, Safari, mobile)
11. **Development Mode** (how to enable debug=True)
12. **Testing Instructions** (how to verify it works)
13. **Troubleshooting** (common issues: port in use, missing modules)

**Format**: Clean markdown with code blocks, lists, and clear sections

---

### Step 4: Code Quality Review
@code-reviewer

Perform comprehensive code quality and structure validation.

**Review Checklist**:

#### 1. Directory Structure Validation (CRITICAL)
```bash
# Verify file structure
find flask_app -type f ! -path '*__pycache__*' | sort

# Expected output:
# flask_app/README.md
# flask_app/app.py
# flask_app/requirements.txt
# flask_app/templates/index.html

# CRITICAL CHECK: Ensure app.py is NOT in templates/
find flask_app/templates -name "app.py"
# Must return EMPTY (no results)
```

**If structure is incorrect**: STOP and report error immediately with fix instructions.

#### 2. Python Code Quality
```bash
# Run flake8 on Python files
cd flask_app && flake8 app.py --max-line-length=88
```

**Check for**:
- PEP 8 compliance (no flake8 errors)
- All functions have docstrings
- No unused imports
- Proper error handling
- Production-safe configuration (debug=False)

#### 3. Flask Best Practices
- ✅ Error handlers (404, 500) present
- ✅ render_template() used correctly
- ✅ Port 5010 specified
- ✅ Host set to 0.0.0.0
- ✅ debug=False for production

#### 4. HTML/CSS Quality
- ✅ Valid HTML5 structure
- ✅ Responsive meta tags present
- ✅ Jinja2 variables used correctly
- ✅ Responsive CSS with media queries
- ✅ Modern design (animations, glassmorphism)

#### 5. Requirements.txt
- ✅ All Flask dependencies listed
- ✅ Versions pinned
- ✅ No missing dependencies

#### 6. Documentation
- ✅ README.md is comprehensive
- ✅ Installation instructions clear
- ✅ Usage examples provided
- ✅ Troubleshooting section included

**Output Format**:
```
🎯 CODE REVIEW RESULTS

📁 Structure: [PASS/FAIL]
   ✅ app.py location: flask_app/app.py
   ✅ templates location: flask_app/templates/
   ✅ All files correctly placed

🐍 Python Quality: [PASS/FAIL]
   ✅ flake8: No errors
   ✅ Docstrings: Present in all functions
   ✅ Error handlers: Implemented

🎨 Frontend Quality: [PASS/FAIL]
   ✅ HTML5: Valid structure
   ✅ Responsive: Mobile-friendly
   ✅ Design: Modern and clean

📦 Dependencies: [PASS/FAIL]
   ✅ All Flask dependencies present

📚 Documentation: [PASS/FAIL]
   ✅ Comprehensive README

🎉 FINAL VERDICT: [READY FOR PRODUCTION / NEEDS FIXES]
```

If any issues found, provide:
- Specific file and line numbers
- Clear explanation of the issue
- Concrete fix recommendation

---

## ✅ Completion Criteria

The project is complete when:
1. ✅ All 4 files created in correct locations
2. ✅ flake8 passes with zero errors
3. ✅ Directory structure validated
4. ✅ Code reviewer gives "READY FOR PRODUCTION" verdict
5. ✅ No critical or high-priority issues remain

---

## 📋 Technical Specifications

**Language**: Python 3.8+
**Framework**: Flask 3.0.0
**Port**: 5010
**Debug Mode**: False (production)
**Template Engine**: Jinja2
**Styling**: Pure CSS (no frameworks)
**Design Pattern**: Glassmorphism with animations
**Responsive**: Mobile-first approach

---

## 🎯 Success Metrics

- **Code Quality**: 100% PEP 8 compliant
- **Structure**: Correct Flask directory layout
- **Security**: Production-safe configuration
- **UX**: Smooth animations, responsive design
- **Documentation**: Complete setup and usage instructions
- **Validation**: All checks pass

---

**Note**: Each agent should complete their assigned tasks fully before the next agent begins. Work sequentially through Steps 1-4.
