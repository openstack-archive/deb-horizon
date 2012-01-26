==================
Contributing Guide
==================

First and foremost, thank you for wanting to contribute! It's the only way
open source works!

Before you dive into writing patches, here are some of the basics:

* Project page: http://launchpad.net/horizon
* Bug tracker: https://bugs.launchpad.net/horizon
* Source code: https://github.com/openstack/horizon
* Code review: https://review.openstack.org/#q,status:open+project:openstack/horizon,n,z
* Jenkins build status: https://jenkins.openstack.org/view/Horizon/

Making Contributions
====================

We'll start by assuming you've got a working checkout of the repository (if
not then please see the :doc:`quickstart`).

Second, you'll need to take care of a couple administrative tasks:

1. Create an account on Launchpad.
2. Sign the `OpenStack Contributor License Agreement`_ and follow the associated
   instructions to verify your signature.
3. Request to join the `OpenStack Contributors`_ team on Launchpad.
4. Join the `Horizon Developers`_ team on Launchpad.
5. Follow the `instructions for setting up git-review`_ in your
   development environment.

Whew! Got that all that? Okay! You're good to go.

The easiest way to get started with Horizon's code is to pick a bug on
Launchpad that interests you, and start working on that. Alternatively, if
there's an OpenStack API feature you would like to see implemented in Horizon
feel free to try building it.

Once you've made your changes, there are a few things to do:

* Make sure the unit tests pass: ``./run_tests.sh``
* Make sure PEP8 is clean: ``./run_tests.sh --pep8``
* Make sure your code is up-to-date with the latest master: ``git pull --rebase``
* Finally, run ``git review`` to upload your changes to Gerrit for review.

The Horizon core developers will be notified of the new review and will examine
it in a timely fashion, either offering feedback or approving it to be merged.
If the review is approved, it is sent to Jenkins to verify the unit tests pass
and it can be merged cleanly. Once Jenkins approves it, the change will be
merged to the master repository and it's time to celebrate!

.. _`OpenStack Contributor License Agreement`: http://wiki.openstack.org/CLA
.. _`OpenStack Contributors`: https://launchpad.net/~openstack-cla
.. _`Horizon Developers`: https://launchpad.net/~horizon
.. _`instructions for setting up git-review`: http://wiki.openstack.org/GerritWorkflow

Code Style
==========

Python
------

We follow PEP8_ for all our Python code, and use ``pep8.py`` (available
via the shortcut ``./run_tests.sh --pep8``) to validate that our code
meets proper Python style guidelines.

.. _PEP8: http://www.python.org/dev/peps/pep-0008/

Django
------

Additionally, we follow `Django's style guide`_ for templates, views, and
other miscellany.

.. _Django's style guide: https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/

JavaScript
----------

As a project, Horizon adheres to code quality standards for our JavaScript
just as we do for our Python. To that end we recommend (but do not strictly
enforce) the use of JSLint_ to validate some general best practices.

The default options are mostly good, but the following accommodate some
allowances we make:

* Set ``Indentation`` to ``2``.
* Enable the ``Assume console, alert, ...`` option.
* Enable the ``Assume a browser`` option.
* Enable the ``Tolerate missing 'use strict' pragma`` option.
* Clear the ``Maximum number of errors`` field.
* Add ``horizon,$`` to the ``Predefined`` list.

.. _JSLint: http://jslint.com/

CSS
---

Style guidelines for CSS are currently quite minimal. Do your best to make the
code readable and well-organized. Two spaces are preferred for indentation
so as to match both the JavaScript and HTML files.

HTML
----

Again, readability is paramount; however be conscientous of how the browser
will handle whitespace when rendering the output. Two spaces is the preferred
indentation style to match all front-end code.

Documentation
-------------

Horizon's documentation is written in reStructuredText and uses Sphinx for
additional parsing and functionality, and should follow
standard practices for writing reST. This includes:

* Flow paragraphs such that lines wrap at 80 characters or less.
* Use proper grammar, spelling, capitalization and punctuation at all times.
* Make use of Sphinx's autodoc feature to document modules, classes
  and functions. This keeps the docs close to the source.
* Where possible, use Sphinx's cross-reference syntax (e.g.
  ``:class:`~horizon.foo.Bar```) when referring to other Horizon components.
  The better-linked our docs are, the easier they are to use.

Be sure to generate the documentation before submitting a patch for review.
Unexpected warnings often appear when building the documentation, and slight
reST syntax errors frequently cause links or cross-references not to work
correctly.
