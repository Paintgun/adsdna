# AdsDNA by Paintgun

![ci](https://github.com/Paintgun/pg-model-building/workflows/ci/badge.svg)

The application represents a Python app with

* jobs and REST API to build models and deliver models results

## Dissection of project files

Let's look at all files that this project is composed of, and what are the points where you'll add functionality:

| Files                                | Meaning                                                                             |
|--------------------------------------|-------------------------------------------------------------------------------------|
| [.github](.github)                   | Describes CI/CD processes implemented with GitHub Actions                           |
| [app](app)                           | Contains main code of the application like API, business logic as well as DAO level |
| [requirements.txt](requirements.txt) | Specifies what python packages are required to run the project                      |

## Running the project locally

### Using virtualenv

```bash
pip install virtualenv
virtualenv venv --python=python3.9
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Using conda env

```bash
conda create --name venv python=3.9
conda activate venv
pip install -r requirements.txt
```

### Using Intellij IDEA

Prerequisite: installed locally Python SDK via Anaconda or Miniconda or anything else

* install "Python" plugin
* configure Python SDK for the project
* install all dependencies from `requirements.txt` (IntelliJ suggests it)
* when the project is configured run the main Python file to start the app

## Continuous Integration

CI is done via [GitHub Actions](https://github.com/features/actions), located in the `.github/workflows` folder of each repository.

We use the `master` or `main` branch for all deployments and work with final project versions only (no SNAPSHOTs). There is
also a GitHub action to verify that the app version has been increased before merging to `master`. We use
[semantic versioning](https://semver.org/).

`.github/workflows` folder contains actions that define CI process with following details

* `ci.yml` builds and runs tests and lints (on a push to any branch)
* `pr-version-check.yml` compares the project versions of the current branch(or HEAD), and the master (on any PR to master)
* `release-and-publish-image.yml` creates and publishes a GitHub release from the merging branch (on a merged PR to master),
  builds a Docker image, publishes it to the organisation's Container registry, and deploys the container to Digital Ocean hosts

The whole CI is covered by these actions and as a result on every merged PR to master

* a new git tag is created
* a new GitHub release is published
* a new Docker image is published
* the image is deployed to a needed environment

## Docker

A Dockerfile is configured for building a project image.

```
docker build -t pg-model-building .
docker run -i -p 5000:5000 \
--env ENV=local \
cat-api
```

## Static analysis and checks

* [GitHub Actions builds, tests, and deploys your code right from GitHub](https://github.com/features/actions)
* [black - Code analysis for Python](https://pypi.org/project/black/).

```
# install black locally
pip install black

# when installed, run it in the main folder
black .
```

* [Markdown lint tool](https://github.com/markdownlint/markdownlint). See `.mdlrc` for rules customization. Used via GitHub Actions.

* [EditorConfig helps maintain consistent coding styles](https://editorconfig.org/). See `.editorconfig` file.

* [Dependabot creates pull requests to keep your dependencies secure and up-to-date](https://dependabot.com/). See `.github/dependabot.yml`.
