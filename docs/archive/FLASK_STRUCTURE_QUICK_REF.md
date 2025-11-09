# Flask File Structure - Quick Reference

## ✅ CORRECT Structure

```
generated_code/
└── flask_app/                         ← Application directory
    ├── app.py                         ← Main Flask app HERE!
    ├── requirements.txt               ← Dependencies
    ├── README.md                      ← Documentation
    ├── config.py                      ← Configuration (optional)
    │
    ├── templates/                     ← Jinja2 templates
    │   ├── base.html
    │   ├── index.html
    │   └── about.html
    │
    └── static/                        ← Static assets (optional)
        ├── css/
        │   └── style.css
        ├── js/
        │   └── main.js
        └── images/
            └── logo.png
```

---

## ❌ COMMON MISTAKES

### Mistake #1: app.py inside templates/

```
flask_app/
├── requirements.txt
└── templates/
    ├── app.py          ❌ WRONG! Should be at flask_app/app.py
    └── index.html
```

**Why wrong**: Flask won't run, templates won't load

---

### Mistake #2: Missing flask_app subdirectory

```
generated_code/
├── app.py              ❌ WRONG! Should be in flask_app/
├── requirements.txt
└── templates/
    └── index.html
```

**Why wrong**: Doesn't follow Flask conventions, messy structure

---

### Mistake #3: Templates at wrong level

```
generated_code/
├── flask_app/
│   └── app.py
└── templates/          ❌ WRONG! Should be inside flask_app/
    └── index.html
```

**Why wrong**: Flask can't find templates (TemplateNotFound)

---

## 🔍 Verification Commands

### Check Structure
```bash
find flask_app -type f | sort
```

**Expected output:**
```
flask_app/app.py
flask_app/requirements.txt
flask_app/templates/index.html
```

### Check for app.py in wrong location
```bash
find flask_app/templates -name "app.py"
```

**Expected output:** (empty - no results)

### Check if app.py exists at root
```bash
ls flask_app/app.py
```

**Expected output:** `flask_app/app.py`

---

## 📝 File Path Examples

### When using Write tool:

#### ✅ CORRECT Paths:
```python
# Main application
file_path: "/home/dev/claude_dev/claude_swarm/generated_code/flask_app/app.py"

# Template
file_path: "/home/dev/claude_dev/claude_swarm/generated_code/flask_app/templates/index.html"

# Static CSS
file_path: "/home/dev/claude_dev/claude_swarm/generated_code/flask_app/static/css/style.css"

# Requirements
file_path: "/home/dev/claude_dev/claude_swarm/generated_code/flask_app/requirements.txt"
```

#### ❌ WRONG Paths:
```python
# app.py in templates (WRONG!)
file_path: "/home/dev/claude_dev/claude_swarm/generated_code/flask_app/templates/app.py"

# Missing flask_app subdirectory (WRONG!)
file_path: "/home/dev/claude_dev/claude_swarm/generated_code/app.py"

# Templates at wrong level (WRONG!)
file_path: "/home/dev/claude_dev/claude_swarm/generated_code/templates/index.html"
```

---

## 🚀 Running the App

### From correct structure:
```bash
cd /home/dev/claude_dev/claude_swarm/generated_code/flask_app
pip install -r requirements.txt
python app.py
```

### This WILL WORK because:
- ✅ app.py is at flask_app root
- ✅ templates/ is a subdirectory
- ✅ Flask knows where to find everything

---

## 🔧 Fixing Wrong Structure

### If app.py is in templates/:
```bash
cd /home/dev/claude_dev/claude_swarm/generated_code/flask_app
mv templates/app.py ./app.py
```

### If missing flask_app subdirectory:
```bash
cd /home/dev/claude_dev/claude_swarm/generated_code
mkdir flask_app
mv app.py requirements.txt flask_app/
mv templates flask_app/
```

---

## 📚 Why This Structure?

### Flask Conventions:
1. **app.py at root** - Entry point of application
2. **templates/ subdirectory** - Flask looks here by default
3. **static/ subdirectory** - Flask serves static files from here
4. **Flat is better than nested** - Easy to navigate

### Benefits:
- ✅ Flask auto-discovers templates
- ✅ Static files served correctly
- ✅ Easy deployment
- ✅ Standard conventions
- ✅ IDE support works properly

### Consequences of wrong structure:
- ❌ `TemplateNotFound` errors
- ❌ `FileNotFoundError` when running
- ❌ Static files return 404
- ❌ Imports fail
- ❌ Deployment breaks

---

## 💡 Remember

**Golden Rule**: `app.py` should ALWAYS be at the root of `flask_app/`, NEVER inside `templates/` or `static/`!

**Quick Check**: If you can't run `python app.py` from `flask_app/` directory, structure is wrong!

**Code Reviewer**: ALWAYS check structure FIRST before reviewing code!

---

## 📖 See Also

- `flask_CLAUDE.md` - Line 445: Full documentation
- `prompts/flask-developer.md` - Developer guidelines
- `prompts/code-reviewer.md` - Validation checklist

---

**Last Updated**: 2025-10-24
**Status**: Production Ready ✅
