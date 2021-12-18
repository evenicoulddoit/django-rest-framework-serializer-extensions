# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
* Introduced `black` and `isort` to standardise coding style
* Restructures requirements to create single source of truth
* Drops `./runtest` executable, `pytest` now direct route

## [2.0.1] - 2020-09-20
### Fixed
* Removed `import_local()`, use Django's in-built `import_string()` method
  instead. This allows compatibility with apps installed via an
  [`AppConfig`](https://docs.djangoproject.com/en/3.0/ref/applications/#for-application-users)
  rather than the older approach of pointing to the package.

## [2.0.0] - 2019-12-14
### Added
* Support for Django 3.0

### Removed
* Support for Python 2 (EOL 2020)

---

## [1.0.0] - 2019-04-21
### Fixed
* Using the `order` or `excludes` keywords retains the original field ordering

## [0.6.0] - 2018-07-02
### Added
* Ability to automatically optimize the queryset used to generate the
  response. This feature is disabled by default, and is experimental

## [0.5.4] - 2017-12-23
### Fixed
* Package build issues when using Python3 (see #15 - thanks @KyeRussell)

### Changed
* Bumps dependencies and Django support to include Django 2

## [0.5.3] - 2017-09-17
### Fixed
* Allow compound local imports (see #13 - thanks @mhotwagner)

## [0.5.2] - 2017-06-19
### Fixed
* Support Rest Framework JavaScript API client

## [0.5.1] - 2017-04-11
### Fixed
* Support expanding non-model serializers

## [0.5.0] - 2017-01-20
### Added
* `read_only=False` field definition support
