from argparse import ArgumentParser
from pathlib import Path
import re
from typing import Any, Union, cast

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    send_from_directory,
)
from werkzeug.middleware.proxy_fix import ProxyFix

from lib.nusmods import nusmods_link_of_code
from src.history.api import (
    INF,
    SEMESTERS,
    STUDENT_TYPES,
    get_all_data,
    get_available_years,
    get_latest_year_and_sem_with_data,
    get_pdf_filepath,
    get_round_numbers,
    pdf_exists,
)

app = Flask(__name__)
# nginx supplies X-Forwarded-Prefix=/courserekt so url_for() emits subpath-safe URLs.
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)  # type: ignore[method-assign]
BASE_DIR = Path(__file__).resolve().parent


def format_acad_year(year: str) -> str:
    """Format a compact academic year such as 2627 as 26/27."""
    return f"{year[:2]}/{year[2:]}"


@app.context_processor
def context_processor() -> dict[str, Any]:
    """Expose read-only helpers used by the history template."""
    return {
        "INF": INF,
        "available_years": get_available_years(),
        "format_acad_year": format_acad_year,
        "pdf_exists": pdf_exists,
        "get_round_numbers": get_round_numbers,
    }


@app.after_request
def add_security_headers(response: Response) -> Response:
    """Apply browser security defaults to every response."""
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "connect-src 'none'; "
        "font-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "img-src 'self' data:; "
        "object-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = (
        "camera=(), geolocation=(), microphone=(), payment=(), usb=()"
    )
    return response


@app.route("/", methods=["GET", "POST"])
def history() -> str:
    """Display course history for a selected dataset."""
    latest_year, latest_semester = get_latest_year_and_sem_with_data()
    year = request.form.get("year", latest_year)
    semester = request.form.get("semester", latest_semester)
    student_type = request.form.get("type", "ug")

    if year not in get_available_years():
        abort(400, description="Unknown academic year.")
    if semester not in SEMESTERS:
        abort(400, description="Unknown semester.")
    if student_type not in STUDENT_TYPES:
        abort(400, description="Unknown student type.")

    output, error = [], None
    try:
        output = get_all_data(year, semester, student_type)
    except ValueError as exc:
        error = exc

    return render_template(
        "history.html",
        output=output,
        error=error,
        year=year,
        semester=semester,
        student_type=student_type,
    )


@app.get("/healthz")
def healthz() -> tuple[dict[str, str], int]:
    """Return a minimal liveness response for the container health check."""
    return {"status": "ok"}, 200


@app.get("/nusmods/<string:code>")
def nusmods_course(code: str) -> Response:
    """Redirect a validated course code to its NUSMods page."""
    if not re.fullmatch(r"[A-Z]{1,6}[0-9]{4}[A-Z]{0,4}", code):
        abort(404)
    return cast(Response, redirect(nusmods_link_of_code(code), code=302))


@app.route(
    "/pdfs/<int:year>/<int:semester>/<string:student_type>/"
    "round_<int:round_num>.pdf"
)
def serve_pdf(
    year: Union[str, int],
    semester: Union[str, int],
    student_type: str,
    round_num: Union[str, int],
) -> Response:
    """Serve one bundled NUS CourseReg report."""
    year_text = str(year)
    semester_text = str(semester)
    round_text = str(round_num)
    if (
        year_text not in get_available_years()
        or semester_text not in SEMESTERS
        or student_type not in STUDENT_TYPES
        or int(round_text) not in get_round_numbers(year_text)
        or not pdf_exists(year_text, semester_text, student_type, round_text)
    ):
        abort(404)

    filepath = get_pdf_filepath(
        year_text, semester_text, student_type, round_text
    )
    return send_from_directory(
        filepath.parent,
        filepath.name,
        conditional=True,
        max_age=86400,
    )


def main() -> None:
    """Run the development server on loopback only."""
    parser = ArgumentParser(description="Web app for CourseRekt")
    parser.add_argument(
        "--port", type=int, default=5000, help="Loopback port where the app is run."
    )
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
