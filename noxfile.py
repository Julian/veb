from pathlib import Path
from tempfile import TemporaryDirectory
import os

import nox

ROOT = Path(__file__).parent
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE = ROOT / "veb"


SUPPORTED = ["3.8", "3.9", "3.10", "pypy3.10", "3.11", "3.12"]
LATEST = SUPPORTED[-1]

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = []


def session(default=True, python=LATEST, **kwargs):  # noqa: D103
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(python=python, **kwargs)(fn)

    return _session


@session(python=SUPPORTED)
def tests(session):
    """
    Run the test suite with a corresponding Python version.
    """
    session.install("virtue", ROOT)

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            posargs = session.posargs[2:]
            github = Path(os.environ["GITHUB_STEP_SUMMARY"])
        else:
            posargs, github = session.posargs[1:], None

        session.install("coverage[toml]")
        session.run("coverage", "run", *posargs, "-m", "virtue", "veb")
        if github is None:
            session.run("coverage", "report")
        else:
            with github.open("a") as summary:
                summary.write("### Coverage\n\n")
                summary.flush()  # without a flush, output seems out of order.
                session.run(
                    "coverage",
                    "report",
                    "--format=markdown",
                    stdout=summary,
                )
    else:
        session.run("virtue", *session.posargs, "veb")


@session(tags=["build"])
def build(session):
    """
    Build a distribution suitable for PyPI and check its validity.
    """
    session.install("build", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
        session.run("twine", "check", "--strict", tmpdir + "/*")


@session(tags=["style"])
def style(session):
    """
    Check Python code style.
    """
    session.install("ruff")
    session.run("ruff", "check", ROOT, __file__)
