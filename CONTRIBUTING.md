# Contributing to cuvis.python

This document covers the branch model, the version scheme, the changelog conventions and the release process.
For bug reports and questions use [GitHub Issues](https://github.com/cubert-hyperspectral/cuvis.python/issues).

## Branch model

| Branch | Role |
| --- | --- |
| `main` | The latest released wrapper state for the latest released cuvis SDK. Every commit on `main` is a release and carries a `v*` tag. Never receives direct pushes. |
| `develop` | Integration branch for the next release. All feature work lands here. |
| `feature/*` | One branch per change, cut from `develop`, merged back into `develop` by pull request. |
| `hotfix/*` | Cut from `main` when a released version needs a fix before `develop` is ready to release. Merged into `main` by pull request, tagged, then merged back into `develop`. |
| `release/vX.Y` | Maintenance branch for an older SDK line that still receives wrapper revisions. Cut from the corresponding tag on demand. |

```
feature/*  ->  develop  ->  main  (tag vX.Y.Z.W)
hotfix/*   ->  main     (tag vX.Y.Z.W)  ->  develop
```

A pull request into `develop` or `main` must pass the `ci.yml` lint and test jobs.

## Version scheme

Versions are `MAJOR.MINOR.PATCH.TWEAK`, always with all four components.

- `MAJOR.MINOR.PATCH` is the cuvis SDK release this wrapper targets.
  It is not chosen by the wrapper; it follows the SDK.
- `TWEAK` counts wrapper-only revisions against that same SDK release, starting at `0`.

Examples:

| Version | Meaning |
| --- | --- |
| `3.5.3.0` | First wrapper release for cuvis SDK 3.5.3. |
| `3.5.3.1` | Wrapper fix on top of it; the SDK is still 3.5.3. |
| `3.5.4.0` | First wrapper release for cuvis SDK 3.5.4. |

Two consequences worth knowing:

- PEP 440 treats `3.5.3.0` and `3.5.3` as the same version, so only one of the two forms may ever be published for a given release.
  Tags created before this scheme was written down use the three-component form (`v3.5.3` is release `3.5.3.0`); everything from `v3.5.3.2` onward is four-component.
- A `TWEAK` bump never widens or narrows the `cuvis-il` requirement in `pyproject.toml`.
  If the interface layer requirement changes, the SDK it targets changed, so the change belongs in a `MAJOR.MINOR.PATCH` release.

The version lives in exactly one place: `[project].version` in `pyproject.toml`.
The git tag is `v` followed by that value, and the release workflow refuses to publish when the two disagree.

## Development setup

```bash
python -m pip install -e ".[test,dev]"
```

The wrapper needs the cuvis SDK and the matching `cuvis-il` interface layer installed on the machine.
The container image `cubertgmbh/cuvis_pyil:<sdk-version>-ubuntu24.04` ships both and is what CI uses.

Run the checks the way CI runs them:

```bash
ruff format --check .
ruff check .
pytest
```

`ruff format` is authoritative for formatting; do not hand-format around it.
The lint rule set is configured in `[tool.ruff.lint]` in `pyproject.toml` and is deliberately narrow.
Widening it is a separate, self-contained pull request, never a side effect of a feature.

## Changelog conventions

Every user-visible change is recorded in `CHANGELOG.md` under `## [Unreleased]` in the same pull request that makes the change.
The file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and is validated by `scripts/check_changelog.py`, which CI runs on every pull request.

### Structure

A release section is a version in brackets, a release date, an SDK statement, and then the change sections:

```markdown
## [3.5.3.2] - 2026-08-19

Targets cuvis SDK 3.5.3.
Wrapper-only revision.

### Fixed

- `cuvis.cube_utils.ImageData` - reading a qmini point spectrum failed because the `1 x 1 x N` buffer shape was not handled in the indexing path.
```

Rules the validator enforces:

- Release headers are `## [<version>] - <YYYY-MM-DD>`, plus one optional `## [Unreleased]` at the top.
- Versions descend down the file, and no version appears twice.
- Section headings are `### ` followed by exactly one of `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`, in that order, and each appears at most once per release.
- Every line inside a section is a `- ` bullet or an indented continuation line.

### Entry wording

Each bullet names what changed first, then states the change with one of the predicates below.
The subject is the fully qualified dotted path in backticks (`cuvis.Module.Class.member`), or a non-API scope in backticks (`pyproject.toml`, `CI`, `tests/`, `README.md`).
One sentence per bullet; a second sentence goes on its own indented continuation line.

| Kind of change | Required form |
| --- | --- |
| New symbol | `` `path` - new <class/enum/function/method/property/field/enum member>[, <default or type>]. `` |
| New parameter | `` `path` - new parameter `name: Type = default`. `` |
| Parameter default added | `` `path` - parameter `name` gained the default `X`. `` |
| Type change | `` `path` - type changed from `A` to `B`. `` |
| Default change | `` `path` - default changed from `A` to `B`. `` |
| Return type change | `` `path` - return type changed from `A` to `B`. `` |
| Field becomes property | `` `path` - field became a <read-only property / property with setter>. `` |
| Rename | `` `path` - renamed to `newpath`. `` |
| Removal | `` `path` - removed; <use X instead / reason>. `` |
| Deprecation | `` `path` - deprecated; <replacement>, removal planned for <version>. `` |
| Behaviour fix | `` `path` - <what went wrong and why>. `` |
| Dependency change | `` `pyproject.toml` - `<dep>` requirement raised from `A` to `B`. `` |

Which section a change belongs in follows from the predicate: new symbols and parameters go under `Added`, type/default/signature changes under `Changed`, removals under `Removed`, behaviour corrections under `Fixed`.
A change that is both (a field that became a property, dropping the old setter) is listed once, under the section describing what callers must react to.

Do not write commit subjects, pull request numbers or author names into the changelog.
The git history already records those, and they say nothing about the API.

## Releasing

### One-time repository setup

The release workflow depends on settings that live outside the repository:

- **Trusted publishers.** PyPI and TestPyPI bind a trusted publisher to a specific workflow file name.
  The publisher for `cuvis` must name `release.yml`; it previously named `publish_version.yml`, so it has to be
  updated once on both indexes or the publish step fails with an OIDC error.
- **Environments.** `testpypi` and `pypi` must exist under Settings -> Environments.
  `pypi` carries the required reviewers that make step 7 below a human gate; without them the release
  publishes unattended.
- **Branch protection.** `main` and `develop` require the `Lint`, `Changelog` and `Tests` checks from
  `ci.yml`, and `main` additionally forbids direct pushes.

### Regular release from `develop`

1. On `develop`, confirm which SDK version the wrapper targets and that `cuvis-il` in `pyproject.toml` matches it.
2. Rename `## [Unreleased]` to `## [X.Y.Z.W] - <today>` and add the SDK statement lines beneath it.
   Add a fresh empty `## [Unreleased]` above it.
3. Set `[project].version` in `pyproject.toml` to `X.Y.Z.W`.
4. Run `ruff format --check . && ruff check . && pytest && python scripts/check_changelog.py`.
5. Open a pull request `develop` -> `main` titled `release: vX.Y.Z.W` and merge it once CI is green.
6. Tag the merge commit on `main` and push the tag:

   ```bash
   git checkout main && git pull
   git tag -a vX.Y.Z.W -m "cuvis X.Y.Z.W"
   git push origin vX.Y.Z.W
   ```

7. `release.yml` validates the tag, builds, publishes to TestPyPI, and then waits for approval on the `pypi` environment before publishing to PyPI and creating the GitHub Release.
8. Merge `main` back into `develop` so the release commit is an ancestor of both.

### Hotfix release from `main`

Same as above, except the branch is `hotfix/<slug>` cut from `main`, the pull request targets `main` directly, only `TWEAK` increases, and step 8 becomes mandatory rather than tidy-up.

### If a release goes wrong

A published PyPI version cannot be replaced.
Fix forward with the next `TWEAK`; yank on PyPI only when the artifact is actively harmful.
Delete the tag and re-tag only while the release workflow has not yet published anything.
