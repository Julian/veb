from pathlib import Path
import os

import nox

ROOT = Path(__file__).parent
PYPROJECT = ROOT / "pyproject.toml"
PACKAGE = ROOT / "veb"


nox.options.sessions = []


def session(default=True, **kwargs):
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(**kwargs)(fn)

    return _session


@session(python=["3.8", "3.9", "3.10", "3.11", "pypy3"])
def tests(session):
    session.install("virtue", ROOT)

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            posargs = session.posargs[2:]
            github = os.environ["GITHUB_STEP_SUMMARY"]
        else:
            posargs, github = session.posargs[1:], None

        session.install("coverage[toml]")
        session.run("coverage", "run", *posargs, "-m", "virtue", "veb")

        if github is None:
            session.run("coverage", "report")
        else:
            with open(github, "a") as summary:
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
    session.install("build")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)


@session(tags=["style"])
def readme(session):
    session.install("build", "twine")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
    session.run("python", "-m", "twine", "check", "--strict", tmpdir + "/veb*")


@session()
def secrets(session):
    session.install("detect-secrets")
    session.run("detect-secrets", "scan", ROOT)


@session(tags=["style"])
def style(session):
    session.install("ruff")
    session.run("ruff", "check", ROOT)


@session(default=False)
def bandit(session):
    session.install("bandit")
    session.run("bandit", "--recursive", PACKAGE)
