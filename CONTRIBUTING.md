
# Contributing guide

## Note:
1. Always check code version from dev branch before coding.
```
git checkout dev
git pull
```
2. Please consider setting a variable in the .env file and use config.py to load the environment variable.
Sometimes we don't need to update MPXSonar code for all query purposes; if some functions are not related to MPXSonar or some query can easily be implemented, please use DB manager (interface) to communicate to the database instance.

## If you don't install dependencies yet

```
conda create -n mpxsonar-dev python=3.9 poetry fortran-compiler nox pre-commit emboss=6.6.0
conda activate mpxradar-dev
git config blame.ignoreRevsFile .git-blame-ignore-revs  # ignore black reformatting when doing git blame
pre-commit install  # install pre-commit hooks for formatting and linting
poetry install  # install current source of covsonar and its dependencies
```

## Before Commit/Push
1. Self-review
    + Check the current branch.
    + Confirm the changes meet the goals
2. Run python-format checking -> `pre-commit run --all-files`. (In most cases, this command will fix all the problems if found) however, sometimes, some errors cannot be solved automatically. Hence
you have to fix it manually according to the error message; otherwise, you will not be allowed to commit and push.

## Pull Request
When you're finished with the changes, create a pull request, also known as a PR.
+ Don't forget to link PR to the issue if you are solving one.

# Add/Update MPXsonar

## First time add MPXsonar
Add MPXsonar repository into this respository like
```
git subtree add --prefix pages/libs/mpxsonar https://github.com/rki-mf1/MpoxSonar dev --squash
```

## Pull new MPXsonar commits
Pull any new updates to the subtree from the remote.
```
git subtree pull --prefix pages/libs/mpxsonar https://github.com/rki-mf1/MpoxSonar dev --squash
```

## Updating/Pushing to the subtree remote repository
If you make a change to anything in subtree the commit will be stored in the MPXRadar-frontend repository and its logs. To update the subtree remote repository with that commit, you must run the same command, excluding --squash and replacing pull for push.
```
git subtree push --prefix pages/libs/mpxsonar https://github.com/rki-mf1/MpoxSonar dev
```

Note: Normally, we don't update the MPXsonar from the MPXRadar-frontend site, but it can happen occasionally. Hence, please consider updating the code from MPXsonar and then using `subtree pull` to update the code.
