# How to contribute

Thanks for looking into contributing to the `arcgis-earthengine-toolbox`. There's many ways to contribute to the toolbox:

* Filing new issues and providing feedback on existing issues
* Contributing examples
* Improving our docs
* Contributing code

All types of contributions are welcome and are a key piece to making the `arcgis-earthengine-toolbox` work well as a community project.

## Before you begin

### Review our community guidelines

This project follows
[Google's Open Source Community Guidelines](https://opensource.google/conduct/).

## Submitting a GitHub issue

You can submit a [GitHub issue](https://github.com/gee-community/arcgis-earthengine-toolbox/issues) for any questions, feature requests, or bug reports.

When submitting a GitHub issue, please provide the following information:

* A clear and concise description of the issue
* The steps to reproduce the issue
* The expected behavior
* The actual behavior
* The ArcGIS Pro version and the version of the toolbox you are using

We have created template for feature requests and bug reports. Please use them when submitting a GitHub issue.

## Contributing examples

## Contributing code and documentation

To contribute code and documentation, follow these steps:

1. Fork the latest `arcgis-earthengine-toolbox` into your GitHub account.

2. Clone the forked repository to your local machine and add the original repository as a remote. This will allow you to pull in the latest changes from the original repository.

    ```bash
    git clone https://github.com/<your-github-username>/arcgis-earthengine-toolbox.git
    cd arcgis-earthengine-toolbox
    git remote add upstream https://github.com/gee-community/arcgis-earthengine-toolbox.git
    ```

3. Follow the installation guide in the [docs](docs/03_installation.md) to install the necessary dependencies.

4. Before you do any new work or submit a pull request, please open an issue to discuss the changes you want to make.

5. Create a new, separate branch for each feature or bug fix. Make your changes to the code or documentation.

    ```bash
    git checkout main
    git fetch upstream
    git checkout -b <your-branch-name> upstream/main
    git push -u origin <your-branch-name>
    ```

6. Push your changes to your forked repository.

    ```bash
    git add .
    git commit -m "Your commit message"
    git push
    ```

7. Submit a pull request to the main repository.

8. Wait for the pull request to be reviewed and merged.

### Code quality checks

The `arcgis-earthengine-toolbox` uses the following code quality checks:

* [pre-commit](https://pre-commit.com/) to run checks on the code before it is committed.
* [black](https://black.readthedocs.io/en/stable/) to format the code.
* [codespell](https://github.com/codespell-project/codespell) to check for spelling errors.
* [mypy](https://mypy.readthedocs.io/en/stable/) to check for type errors.
* [pylint](https://pylint.pycqa.org/en/stable/) to check for code style violations.

The pre-commit yaml file currently contains xml file format, black and codespell checks. If you don't have pre-commit installed, run the following command:

```bash
pip install pre-commit
```

To install the pre-commit hooks, run the following command:

```bash
pre-commit install
```

To run the checks manually, run the following command:

```bash
pre-commit run --all-files
```

Since the ArcGIS Pro Python Toolbox does not fully comply with the Python code style, we recommend to run mypy and pylint checks manually as there will be many warnings and errors. Please also note that this package has to be compatible with ArcGIS Pro 3.2 (Python 3.9). Therefore, Python 3.10 type hints (e.g. str | None) are not supported.

## Contribution process

### Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.
