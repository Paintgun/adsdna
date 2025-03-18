# Model Building by Paintgun LTD

![ci](https://github.com/Paintgun/pg-model-building/workflows/ci/badge.svg)

The application represents a Python app with

* a cron job to build models

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

## Way of Working

This part describes how the team structures their work.

### Working Principles

As a team of business and technical people we rely on the following values.

* reliability
* openness
* goals achievement and not "officially" spent working hours
* direct communication and proper feedback to each other
* after the work is done we get together in a nice pub and celebrate our common achievements

### Organizational Basics

* We all know the way of working rules and follow them
* Meetings start and finish in time; the moderator should be in the meeting 2-5 minutes ahead
* Everyone has the right to block time for individual learning and development

### Technological Basics

* We keep all output of work in git (git is the source of truth; if documentation is needed elsewhere it is preferably brought there via export from git)
* Branches are named after the corresponding ticket name
* We do test wherever possible and reasonable; we automate the collection and evaluation of test results
* We use metrics where possible and reasonable (our work should become data driven)

### Working with User Stories

User Stories (US) are defined with a goal to deliver a real business or tech values.
They must be granular and clearly describing what must be achieved.
A US must have all the business details and requirements needed for a proper implementation.
If a US is a technical one then all tech details must be clarified in the analysis phase.

### Retrospectives

Once in two weeks we hold a retrospective meeting to discuss what have been achieved in the last weeks, what went well,
what we didn't like and what we want to change and improve.

### Definition of Ready (DoR)

A user story or task is considered "ready" if all GitHub Actions are green and the corresponding pull request has been approved by other team members.
