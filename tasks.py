from contextlib import contextmanager
import os


from invoke import task


package_name = "pytest_vcr_delete_on_fail"
poetry_pypi_testing = "testpypi"

# Supported python version list - these must also be valid executable in your path
supported_python_versions = ["python3.7", "python3.8", "python3.9", "python3.10"]
# Use the minimum python version required by the package
default_python_bin = supported_python_versions[0]


# By default, target the OLDEST python version
# If the most currently supported python version is desired, use 'inv install -p latest'
@task
def install(c, python=default_python_bin):
    if python == "latest":
        c.run("poetry env use {}".format(supported_python_versions[-1]))
    else:
        c.run("poetry env use {}".format(python))
    c.run("poetry install")


@task
def rm_venv(c):
    c.run("rm -rf .venv")


# Use this to change quickly python version
@task(rm_venv)
def reinstall(c, python=default_python_bin):
    install(c, python)


@task
def build(c):
    c.run("poetry build")


@task(build)
def publish_coverage(c):
    c.run("poetry run coveralls")


@task(build)
def publish_test(c):
    c.run(f"poetry publish -r {poetry_pypi_testing}")


@task(build)
def publish(c):
    c.run("poetry publish")


def get_test_command(s=False, m=None, other_flags=""):
    marks = ""
    if m is not None:
        marks = f" -m {m}"
    capture = ""
    if s:
        capture = " -s"
    return (
        f"poetry run pytest{capture}{marks}{other_flags} --runpytest subprocess tests/"
    )


@task()
def test(c, s=False, m=None):
    c.run(get_test_command(s, m), pty=True)


@task()
def test_spec(c, m=None):
    c.run(get_test_command(m=m, other_flags=" -p no:sugar --spec"), pty=True)


@task()
def test_all_python_version(c, coverage=False):
    python_version_checked = ""
    # Run the tests on an inverted supported_python_versions list, so that the last one is the default one so
    # no reset is needed
    python_version = supported_python_versions.copy()
    python_version.reverse()
    for version in python_version:
        print(f"\n>>> Installing python venv with version: {version}\n")
        reinstall(c, python=version)
        print(f"\n>>> Running tests with version: {version}\n")

        cmd = get_test_command()
        if coverage:
            cmd = get_coverage_test_command()
        result = c.run(cmd, pty=True, warn=True)

        if result.ok:
            python_version_checked += f" {version}"
        else:
            print(f"\n>>> Could not test correctly under {version} - stopping here!")
            exit(1)
    print(f"\n>>> All test passed! Python version tested:{python_version_checked}")
    print(f"\n>>> Current venv python version: {python_version[-1]}")


@task()
def clear_cassettes(c):
    c.run("rm -rf tests/cassettes")
    print("Cleared!")


def get_coverage_test_command(m=None):
    marks = ""
    if m is not None:
        marks = f" -m {m}"
    # This requires a workaround since the target it's a pytest plugin itself
    # See https://pytest-cov.readthedocs.io/en/latest/plugins.html
    return (
        f"COV_CORE_SOURCE={package_name} COV_CORE_CONFIG=.coveragerc COV_CORE_DATAFILE=.coverage.eager "
        + f"poetry run pytest{marks} --runpytest subprocess --cov={package_name} --cov-append"
        + " --cov-report html:coverage/cov_html"
        + " --cov-report xml:coverage/sonarqube/coverage.xml"
        + " --junitxml=coverage/sonarqube/results.xml"
        + " tests/"
    )


@task()
def test_cov(c, m=None):
    c.run("mkdir -p coverage")
    c.run(get_coverage_test_command(m), pty=True)


@task(test_cov)
def html_cov(c):
    c.run("xdg-open coverage/cov_html/index.html")


@task()
def checks(c):
    c.run("poetry run black --check .")
    print("")
    c.run(
        "poetry run mypy pytest_vcr_delete_on_fail/",
        pty=True,
    )


#
# SONARQUBE
#
@contextmanager
def patched_coverage_path(c) -> None:
    """Make sure the path in the coverage file are mapped inside the sonar container."""
    coverage_file = "coverage/sonarqube/coverage.xml"
    pwd = os.getcwd().replace("/", "\\/")
    src = "/usr/src".replace("/", "\\/")
    c.run(f"sed -i 's#{pwd}#{src}#' {coverage_file}")
    try:
        yield
    except Exception as e:
        # Make sure the coverage path are restored even with an error
        c.run(f"sed -i 's#{src}#{pwd}#' {coverage_file}")
        raise e
    c.run(f"sed -i 's#{src}#{pwd}#' {coverage_file}")


@task()
def sonar(c, no_branch=False):
    """Run a sonarqube analysis. It needs docker installed and the .secrets file present."""
    repo_full_path = os.getcwd()
    no_branch_str = ""
    if not no_branch:
        branch = "`git rev-parse --abbrev-ref HEAD`"
        no_branch_str = f'-e SONAR_SCANNER_OPTS="-Dsonar.branch.name={branch}"'

    # Make sure coverage data is up-to-date
    c.run(get_coverage_test_command(), pty=True, warn=True)

    with patched_coverage_path(c):
        c.run(
            "docker run"
            " --rm"
            f" --env-file .secrets"
            f" {no_branch_str}"
            f" -v '{repo_full_path}:/usr/src'"
            f" sonarsource/sonar-scanner-cli"
        )


#
# Docs
#
@task()
def docs_build(c):
    c.run("cd docs; make html")
    print("\n>> Docs built!\n")


@task()
def docs_clean(c):
    c.run("cd docs; make clean")
    print("\n>> Docs cleaned!\n")


@task(docs_clean, docs_build)
def docs_serve(c):
    from livereload import Server

    port = 5500
    server = Server()
    print(">> Serving and watching for changes...\n")
    # Open the docs in the browser
    c.run(f"xdg-open 'http://localhost:{port}'")
    # Watch for changes in rst files; rebuild the html documentation when it happens
    server.watch("README.rst", lambda: docs_build(c))
    server.watch("docs/source/*.rst", lambda: docs_build(c))
    # Serve the builded docs. This will autoreload on change!
    server.serve(root="docs/build/html", port=port)


#
# ACT
#
act_dev_ctx = "act-dev-ci"
act_prod_ctx = "act-prod-ci"
act_secrets_file = ".secrets"


@task
def act_prod(c, cmd=""):
    if cmd == "":
        c.run("act -W .github/workflows/prod.yml", pty=True)
    elif cmd == "shell":
        c.run(
            f"docker exec --env-file {act_secrets_file} -it {act_prod_ctx} bash",
            pty=True,
        )
    elif cmd == "clean":
        c.run(f"docker rm -f {act_prod_ctx}", pty=True)


@task
def act_dev(c, cmd=""):
    if cmd == "":
        c.run("act -W .github/workflows/dev.yml", pty=True)
    elif cmd == "shell":
        c.run(
            f"docker exec --env-file {act_secrets_file} -it {act_dev_ctx} bash",
            pty=True,
        )
    elif cmd == "clean":
        c.run(f"docker rm -f {act_dev_ctx}", pty=True)
