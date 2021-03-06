Link Preview
============

A small plugin for `Nicotine+`_ to display preview information like
title and description about links sent in chats.

Plugin created with `Nicotine+ Plugin Template`_ made by `Nachtalb`_.

Installation
------------

Open Nicotine+ settings, go to *General > Plugins* and click *+ Add
Plugins*. After that download the latest `release`_ and extract it into
the plugins folder.

Remove the version from the folder name. The folder name must stay the
same across version upgrades otherwise you will loose any changed
settings.

Now you can enable the *Link Preview* plugin in the previously
opened plugin settings.


Commands
--------

- ``/lp-update`` manually check for updates.
- ``/lp-reload`` reload the plugin.


Settings
--------

+---------------------+-----------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| Name                | Function                                                                                | Default                                                              |
+=====================+=========================================================================================+======================================================================+
| Check for Updates   | Check for updates on start and periodically                                             | Enabled                                                              |
+---------------------+-----------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| Message Colour      | How the message should be coloured                                                      | Action                                                               |
+---------------------+-----------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| Link Preview        | Template for how to display the information. Available placeholders are:                | ``['* Title: {site_name} {title}', '* Description: {description}']`` |
|                     |                                                                                         |                                                                      |
|                     | - ``{site_name}``: Eg. YouTube, Google & Twitter                                        |                                                                      |
|                     | - ``{title}``: Eg. "Some video title foo bar", "Your search query on google"            |                                                                      |
|                     | - ``{description}``: Eg. "This is some video description on youtube"                    |                                                                      |
|                     | - ``{url}``: The URL which was sent in the chat message                                 |                                                                      |
+---------------------+-----------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| Domain Blacklist    | This may come in useful eg. when you have the YouTube Link Preview plugin active that   | ``[]``                                                               |
|                     | has more detailed information about youtube videos.                                     |                                                                      |
|                     |                                                                                         |                                                                      |
|                     | Prefix any regex with ``r/``.                                                           |                                                                      |
|                     |                                                                                         |                                                                      |
|                     | You can use this regex if you use the YouTube plugin (see plugin description to copy    |                                                                      |
|                     | it): ``r/(?:www\.|m\.)?youtu(?:be\-nocookie\.com|\.be|be\.com)``                        |                                                                      |
+---------------------+-----------------------------------------------------------------------------------------+----------------------------------------------------------------------+
| Domain Whitelist    | Works the same as the blacklist but the other way around. Blacklist will be ignored.    | ``[]``                                                               |
+---------------------+-----------------------------------------------------------------------------------------+----------------------------------------------------------------------+


Contributing
------------

Pull requests are welcome.


License
-------

`MIT`_

.. _Nicotine+: https://nicotine-plus.github.io/nicotine-plus/
.. _Nicotine+ Plugin Template: https://github.com/Nachtalb/nicotine_plus_plugin_template
.. _Nachtalb: https://github.com/Nachtalb
.. _release: https://github.com/Nachtalb/link_preview/releases
.. _MIT: https://github.com/Nachtalb/link_preview/blob/master/LICENSE
