from flask import Flask, request, jsonify, render_template
import subprocess
import tempfile
import os
import html

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run_code():
    data = request.get_json()  # safer to use get_json()
    language = data.get("language", "html").lower()
    user_input = data.get("input", "")

    if language == "python":
        # Unescape and get python code from 'code' key
        python_code = html.unescape(data.get("code", ""))
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(python_code)
            f.flush()
            filename = f.name

        try:
            # Run Python code with user_input piped into stdin
            result = subprocess.run(
                ["python3", filename],  # use python3 explicitly for modern envs
                input=user_input,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout + result.stderr
            if "EOFError" in output:
                output = "Error: No input provided or input ended unexpectedly."
        except subprocess.TimeoutExpired:
            output = "Execution timed out."
        except Exception as e:
            output = f"Error running code: {str(e)}"
        finally:
            os.remove(filename)

        # Return safely escaped output inside <pre>
        return jsonify({"output": f"<pre>{html.escape(output)}</pre>"})

    elif language == "web":
        # Compose full HTML with embedded CSS and JS
        html_code = data.get("html", "")
        css_code = data.get("css", "")
        js_code = data.get("js", "")

        full_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Live Preview</title>
  <style>
  {css_code}
  </style>
</head>
<body>
{html_code}
<script>
try {{
{js_code}
}} catch(e) {{
  document.body.innerHTML += '<pre style="color:red;">' + e + '</pre>';
}}
</script>
</body>
</html>"""
        return jsonify({"output": full_output})

    else:
        return jsonify({"output": "<pre>Unsupported language selected.</pre>"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) 