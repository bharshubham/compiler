from flask import Flask, render_template, request
from checker import run_python_checker, execute_code

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    output = ""
    code = ""
    language = "Python"

    if request.method == "POST":
        code = request.form["code"]
        language = request.form["language"]

        if language == "Python":
            result = run_python_checker(code)
            # Run code only if no type errors
            if result.startswith("No type errors"):
                output = execute_code(code, language)
        else:
            output = execute_code(code, language)
            result = "--- Code Output ---"

    return render_template("index.html", result=result, output=output, code=code, language=language)

if __name__ == "__main__":
    app.run(debug=True)
