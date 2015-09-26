===================
Customizing Horizon
===================

Themes
======

As of the Kilo release, styling for the OpenStack Dashboard can be altered
through the use of a theme. A theme is a directory containing a
``_variables.scss`` file to override the color codes used throughout the SCSS
and a ``_styles.scss`` file with additional styles to load after dashboard
styles have loaded.

To use a custom theme, set ``CUSTOM_THEME_PATH`` in ``local_settings.py`` to
the directory location for the theme (e.g., ``"themes/material"``). The
path can either be relative to the ``openstack_dashboard`` directory or an
absolute path to an accessible location on the file system. The default
``CUSTOM_THEME_PATH`` is ``themes/default``.

Both the Dashboard custom variables and Bootstrap variables can be overridden.
For a full list of the Dashboard SCSS variables that can be changed, see the
variables file at ``openstack_dashboard/static/dashboard/scss/_variables.scss``.

Organizing Your Theme Directory
-------------------------------

A custom theme directory can be organized differently, depending on the
level of customization that is desired, as it can include static files
as well as Django templates.  It can include special subdirectories that will
be used differently: ``static``, ``templates`` and ``img``.

The Static Folder
-----------------

If the theme folder contains a sub-folder called ``static``, then that sub
folder will be used as the **static root of the theme**.  I.e., Horizon will
look in that sub-folder for the _variables.scss and _styles.scss files.
The contents of this folder will also be served up at ``/static/custom``.

The Templates Folder
--------------------

If the theme folder contains a sub-folder ``templates``, then the path
to that sub-folder will be prepended to the ``TEMPLATE_DIRS`` tuple to
allow for theme specific template customizations.

Using the Templates Folder
--------------------------

Any Django template that is used in Horizon can be overridden through a theme.
This allows highly customized user experiences to exist within the scope of
different themes.  Any template that is overridden must adhere to the same
directory structure that the extending template expects.

For example, if you wish to customize the sidebar, Horizon expects the template
to live at ``horizon/_sidebar.html``.  You would need to duplicate that
directory structure under your templates directory, such that your override
would live at ``{CUSTOM_THEME_PATH}/templates/horizon/_sidebar.html``.

The Img Folder
--------------

If the static root of the theme folder contains an ``img`` directory,
then all images contained within ``dashboard/img`` can be overridden by
providing a file with the same name.

For a complete list of the images that can be overridden this way, see:
``openstack_dashboard/static/dashboard/img``

Customizing the Logo
--------------------

If you wish to customize the logo that is used on the splash screen or in the
top navigation bar, then you simply need to create an ``img`` directory under
your theme's static root directory and place your custom ``logo.png`` or
``logo-splash.png`` within it.

If you wish to override the ``logo.png`` using the previous method, and if the
image used is larger than the height of the top navbar, then the image will be
constrained to fit within the height of nav.  You can customize the height of
the top navigation by customizing the SCSS variable: ``$navbar-height``.
If the image's height is smaller than the navbar height, then the image
will retain its original resolution and size, and simply be centered
vertically in the available space.

Prior to the Kilo release the images files inside of Horizon needed to be
replaced by your images files or the Horizon stylesheets needed to be altered
to point to the location of your image.

Changing the Site Title
=======================

The OpenStack Dashboard Site Title branding (i.e. "**OpenStack** Dashboard")
can be overwritten by adding the attribute ``SITE_BRANDING``
to ``local_settings.py`` with the value being the desired name.

The file ``local_settings.py`` can be found at the Horizon directory path of
``openstack_dashboard/local/local_settings.py``.

Changing the Brand Link
=======================

The logo also acts as a hyperlink. The default behavior is to redirect to
``horizon:user_home``. By adding the attribute ``SITE_BRANDING_LINK`` with
the desired url target e.g., ``http://sample-company.com`` in
``local_settings.py``, the target of the hyperlink can be changed.

Modifying Existing Dashboards and Panels
========================================

If you wish to alter dashboards or panels which are not part of your codebase,
you can specify a custom python module which will be loaded after the entire
Horizon site has been initialized, but prior to the URLconf construction.
This allows for common site-customization requirements such as:

* Registering or unregistering panels from an existing dashboard.
* Changing the names of dashboards and panels.
* Re-ordering panels within a dashboard or panel group.

Default Horizon panels are loaded based upon files within the openstack_dashboard/enabled/
folder.  These files are loaded based upon the filename order, with space left for more
files to be added.  There are some example files available within this folder, with the
.example suffix added.  Developers and deployers should strive to use this method of
customization as much as possible, and support for this is given preference over more
exotic methods such as monkey patching and overrides files.

Horizon customization module (overrides)
========================================

Horizon has a global overrides mechanism available to perform customizations that are not
yet customizable via configuration settings.  This file can perform monkey patching and
other forms of customization which are not possible via the enabled folder's customization
method.

This method of customization is meant to be available for deployers of Horizon, and use of
this should be avoided by Horizon plugins at all cost.  Plugins needing this level of
monkey patching and flexibility should instead look for changing their __init__.py file
and performing customizations through other means.

To specify the python module containing your modifications, add the key
``customization_module`` to your ``HORIZON_CONFIG`` dictionary in
``local_settings.py``. The value should be a string containing the path to your
module in dotted python path notation. Example::

    HORIZON_CONFIG = {
        "customization_module": "my_project.overrides"
    }

You can do essentially anything you like in the customization module. For
example, you could change the name of a panel::

    from django.utils.translation import ugettext_lazy as _

    import horizon

    # Rename "User Settings" to "User Options"
    settings = horizon.get_dashboard("settings")
    user_panel = settings.get_panel("user")
    user_panel.name = _("User Options")

Or get the instances panel::

    projects_dashboard = horizon.get_dashboard("project")
    instances_panel = projects_dashboard.get_panel("instances")

And limit access to users with the Keystone Admin role::

    permissions = list(getattr(instances_panel, 'permissions', []))
    permissions.append('openstack.roles.admin')
    instances_panel.permissions = tuple(permissions)

Or just remove it entirely::

    projects_dashboard.unregister(instances_panel.__class__)

You cannot unregister a ``default_panel``. If you wish to remove a
``default_panel``, you need to make a different panel in the dashboard as a
``default_panel`` and then unregister the former. For example, if you wished
to remove the ``overview_panel`` from the ``Project`` dashboard, you could do
the following::

    project = horizon.get_dashboard('project')
    project.default_panel = "instances"
    overview = project.get_panel('overview')
    project.unregister(overview.__class__)

You can also override existing methods with your own versions::

    # Disable Floating IPs
    from openstack_dashboard.dashboards.project.access_and_security import tabs
    from openstack_dashboard.dashboards.project.instances import tables

    NO = lambda *x: False

    tabs.FloatingIPsTab.allowed = NO
    tables.AssociateIP.allowed = NO
    tables.SimpleAssociateIP.allowed = NO
    tables.SimpleDisassociateIP.allowed = NO

You could also customize what columns are displayed in an existing
table, by redefining the ``columns`` attribute of its ``Meta``
class. This can be achieved in 3 steps:

#. Extend the table that you wish to modify
#. Redefine the ``columns`` attribute under the ``Meta`` class for this
   new table
#. Modify the ``table_class`` attribute for the related view so that it
   points to the new table


For example, if you wished to remove the Admin State column from the
:class:`~openstack_dashboard.dashboards.admin.networks.tables.NetworksTable`,
you could do the following::

    from openstack_dashboard.dashboards.project.networks import tables
    from openstack_dashboard.dashboards.project.networks import views

    class MyNetworksTable(tables.NetworksTable):

        class Meta(tables.NetworksTable.Meta):
            columns = ('name', 'subnets', 'shared', 'status')

    views.IndexView.table_class = MyNetworksTable

If you want to add a column you can override the parent table in a
similar way, add the new column definition and then use the ``Meta``
``columns`` attribute to control the column order as needed.

.. NOTE::

    ``my_project.overrides`` needs to be importable by the python process running
    Horizon.
    If your module is not installed as a system-wide python package,
    you can either make it installable (e.g., with a setup.py)
    or you can adjust the python path used by your WSGI server to include its location.

    Probably the easiest way is to add a ``python-path`` argument to
    the ``WSGIDaemonProcess`` line in Apache's Horizon config.

    Assuming your ``my_project`` module lives in ``/opt/python/my_project``,
    you'd make it look like the following::

        WSGIDaemonProcess [... existing options ...] python-path=/opt/python


Button Icons
============

Horizon uses font icons (glyphicons) from Twitter Bootstrap to add icons to buttons.
Please see http://bootstrapdocs.com/v3.1.1/docs/components/#glyphicons for instructions
how to use icons in the code.

To add icon to Table Action, use icon property. Example:

    class CreateSnapshot(tables.LinkAction):
       name = "snapshot"
       verbose_name = _("Create Snapshot")
       icon = "camera"

Additionally, the site-wide default button classes can be configured by
setting ``ACTION_CSS_CLASSES`` to a tuple of the classes you wish to appear
on all action buttons in your ``local_settings.py`` file.


Custom Stylesheets
==================

It is possible to define custom stylesheets for your dashboards. Horizon's base
template ``openstack_dashboard/templates/base.html`` defines multiple blocks that
can be overridden.

To define custom css files that apply only to a specific dashboard, create
a base template in your dashboard's templates folder, which extends Horizon's
base template e.g. ``openstack_dashboard/dashboards/my_custom_dashboard/
templates/my_custom_dashboard/base.html``.

In this template, redefine ``block css``. (Don't forget to include
``_stylesheets.html`` which includes all Horizon's default stylesheets.)::

    {% extends 'base.html' %}

    {% block css %}
      {% include "_stylesheets.html" %}

      {% load compress %}
      {% compress css %}
      <link href='{{ STATIC_URL }}my_custom_dashboard/scss/my_custom_dashboard.scss' type='text/scss' media='screen' rel='stylesheet' />
      {% endcompress %}
    {% endblock %}

The custom stylesheets then reside in the dashboard's own ``static`` folder
``openstack_dashboard/dashboards/my_custom_dashboard/static/
my_custom_dashboard/scss/my_custom_dashboard.scss``.

All dashboard's templates have to inherit from dashboard's base.html::

    {% extends 'my_custom_dashboard/base.html' %}
    ...


Custom Javascript
=================

Similarly to adding custom styling (see above), it is possible to include
custom javascript files.

All Horizon's javascript files are listed in the ``openstack_dashboard/
templates/horizon/_scripts.html`` partial template, which is included in
Horizon's base template in ``block js``.

To add custom javascript files, create an ``_scripts.html`` partial template in
your dashboard ``openstack_dashboard/dashboards/my_custom_dashboard/
templates/my_custom_dashboard/_scripts.html`` which extends
``horizon/_scripts.html``. In this template override the
``block custom_js_files`` including your custom javascript files::

    {% extends 'horizon/_scripts.html' %}

    {% block custom_js_files %}
        <script src='{{ STATIC_URL }}my_custom_dashboard/js/my_custom_js.js' type='text/javascript' charset='utf-8'></script>
    {% endblock %}


In your dashboard's own base template ``openstack_dashboard/dashboards/
my_custom_dashboard/templates/my_custom_dashboard/base.html`` override
``block js`` with inclusion of dashboard's own ``_scripts.html``::

    {% block js %}
        {% include "my_custom_dashboard/_scripts.html" %}
    {% endblock %}

The result is a single compressed js file consisting both Horizon and
dashboard's custom scripts.

Additionally, some marketing and analytics scripts require you to place them
within the page's <head> tag. To do this, place them within the
``horizon/_custom_head_js.html`` file. Similar to the ``_scripts.html`` file
mentioned above, you may link to an existing file::

    <script src='{{ STATIC_URL }}/my_custom_dashboard/js/my_marketing_js.js' type='text/javascript' charset='utf-8'></script>

or you can paste your script directly in the file, being sure to use
appropriate tags::

  <script type="text/javascript">
  //some javascript
  </script>


Customizing Meta Attributes
===========================

To add custom metadata attributes to your project's base template, include
them in the ``horizon/_custom_meta.html`` file. The contents of this file will be
inserted into the page's <head> just after the default Horizon meta tags.
