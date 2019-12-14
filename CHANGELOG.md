### 2.0.0 (2019-12-14)
* Adds support for Django 3.0
* Drops support for Python 2 (EOL 2020)

### 1.0.0 (2019-04-21)
* Using the `order` or `excludes` keywords retains the original field ordering
* Bumping to first major version. Seems this package has enough usage without
  major issues to suggest it's production-ready

### 0.6.0 (2018-07-02)
* Adds the ability to automatically optimize the queryset used to generate
  the response. This feature is disabled by default, and is experimental

### 0.5.4 (2017-12-23)
* Fixes package build issues when using Python3 (see #15 - thanks @KyeRussell)
* Bumps dependencies and Django support to include Django 2

### 0.5.3 (2017-09-17)
* Bugfix to allow compound local imports (see #13 - thanks @mhotwagner)

### 0.5.2 (2017-06-19)
* Bugfix to support Rest Framework JavaScript API client

### 0.5.1 (2017-04-11)
* Bugfix to support expanding non-model serializers

### 0.5.0 (2017-01-20)
* Added `read_only=False` field definition support
