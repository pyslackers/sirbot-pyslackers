============
Contributing
============

First off, thanks for taking the time to contribute!

Contributions are welcome by anybody and everybody. We are not kidding! Looking for help ? Join us on `Slack`_ by requesting an `invite`_.

The rest of this document will be guidelines to contributing to the project. Remember that these are just guidelines, not rules. Use common sense as much as possible.

.. _invite: http://pyslackers.com/
.. _Slack: https://pythondev.slack.com/

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests (if necessary). If you have any questions about how to write tests then ask the community.
2. If the pull request adds functionality update the docs where appropriate.
3. Use a `good commit message`_.

.. _good commit message: https://github.com/spring-projects/spring-framework/blob/30bce7/CONTRIBUTING.md#format-commit-messages

Types of Contributions
----------------------

Report Bugs
^^^^^^^^^^^

The best way to report a bug is to file an `issue <https://github.com/pyslackers/sirbot-pyslackers/issues>`_.

Please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs & Features
^^^^^^^^^^^^^^^^^^^

Look through the github issues for bugs or features request.
Anything tagged with "help-wanted" is open to whoever wants to implement it.

Write Documentation
^^^^^^^^^^^^^^^^^^^

Sirbot-pyslackers could always use more documentation and examples, whether as docstring or guide for setting things up.

Submit Feedback
^^^^^^^^^^^^^^^

The best way to submit feedback is to file an `issue <https://github.com/pyslackers/sirbot-pyslackers/issues>`_.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get started
-----------

Sirbot is built with docker in mind. It is deployed using a docker container, testing should be perform on docker containers as well.

Environment setup
^^^^^^^^^^^^^^^^^

Some environment variable are needed for Sirbot to operate. An example file is provided (`docker/example.env <docker/example.env>`_). To overwrite it and set your own instance variable create a ``sirbot.env`` file in the ``docker`` directory.

Setup a development slack team
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To test the bot it is required to create a development slack team and an app that use workspace token. To create a team click `here <https://slack.com/get-started#create>`_ and to create a workspace app click `here <https://api.slack.com/apps?new_app_token=1>`_.

Deploy a development bot
^^^^^^^^^^^^^^^^^^^^^^^^

To deploy a development version of the bot on your own machine use the `dev.sh <dev.sh>`_ script. It will start a docker stack composed of:

* The bot container
* A postgresql database
* An ngrok instance

Connect to `http://localhost:4040 <http://localhost:4040>`_ to access the ngrok management interface and find your url.

Code style testing
^^^^^^^^^^^^^^^^^^

To run the CI tests use the `test.sh <test.sh>`_ script. It will build a new docker image and run tests on it.
