# Contributing

First off, thanks for taking the time to contribute! Contributions include but are not restricted to:

- Reporting bugs
- Contributing to code
- Writing tests
- Writing documentation

The following is a set of guidelines for contributing.

## A recommended flow of contributing to an Open Source project

This section is for beginners to OSS. If you are an experienced OSS developer, you can skip
this section.

1. First, fork this project to your own namespace using the fork button at the top right of the repository page.
2. Clone the **upstream** repository to local:
   ```sh
   git clone https://github.com/L-Nafaryus/materia.git
   # Or if you prefer SSH clone:
   git clone git@github.com:L-Nafaryus/materia.git
   ```
3. Add the fork as a new remote:
   ```sh
   git remote add fork https://github.com/yourname/materia.git
   git fetch fork
   ```
   where `fork` is the remote name of the fork repository.

/// tip

1. Don't modify code on the master branch, the master branch should always keep track of origin/master.

    To update master branch to date:

    ```sh
    git pull origin master
    # In rare cases that your local master branch diverges from the remote master:
    git fetch origin && git reset --hard master
    ```

2. Create a new branch based on the up-to-date master branch for new patches.
3. Create a Pull Request from that patch branch.

///

## Local development

See [Local development](./local.md)

## Code style

*Soon*

## Realease

*Soon*
