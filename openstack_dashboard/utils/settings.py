#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
from importlib import import_module
import logging
import os
import pkgutil
import six

from horizon.utils import file_discovery
from openstack_dashboard import theme_settings


def import_submodules(module):
    """Import all submodules and make them available in a dict."""
    submodules = {}
    for loader, name, ispkg in pkgutil.iter_modules(module.__path__,
                                                    module.__name__ + '.'):
        try:
            submodule = import_module(name)
        except ImportError as e:
            # FIXME: Make the errors non-fatal (do we want that?).
            logging.warning("Error importing %s" % name)
            logging.exception(e)
        else:
            parent, child = name.rsplit('.', 1)
            submodules[child] = submodule
    return submodules


def import_dashboard_config(modules):
    """Imports configuration from all the modules and merges it."""
    config = collections.defaultdict(dict)
    for module in modules:
        for key, submodule in six.iteritems(import_submodules(module)):
            if hasattr(submodule, 'DASHBOARD'):
                dashboard = submodule.DASHBOARD
                config[dashboard].update(submodule.__dict__)
            elif (hasattr(submodule, 'PANEL')
                  or hasattr(submodule, 'PANEL_GROUP')
                  or hasattr(submodule, 'FEATURE')):
                config[submodule.__name__] = submodule.__dict__
            else:
                logging.warning("Skipping %s because it doesn't have DASHBOARD"
                                ", PANEL, PANEL_GROUP, or FEATURE defined.",
                                submodule.__name__)
    return sorted(six.iteritems(config),
                  key=lambda c: c[1]['__name__'].rsplit('.', 1)[1])


def update_dashboards(modules, horizon_config, installed_apps):
    """Imports dashboard and panel configuration from modules and applies it.

    The submodules from specified modules are imported, and the configuration
    for the specific dashboards is merged, with the later modules overriding
    settings from the former. Then the configuration is applied to
    horizon_config and installed_apps, in alphabetical order of files from
    which the configurations were imported.

    For example, given this setup:

        | foo/__init__.py
        | foo/_10_baz.py
        | foo/_20_qux.py

        | bar/__init__.py
        | bar/_30_baz_.py

    and being called with ``modules=[foo, bar]``, we will first have the
    configuration from ``_10_baz`` and ``_30_baz`` merged, then the
    configurations will be applied in order ``qux``, ``baz`` (``baz`` is
    second, because the most recent file which contributed to it, ``_30_baz``,
    comes after ``_20_qux``).

    Panel specific configurations are stored in horizon_config. Dashboards
    from both plugin-based and openstack_dashboard must be registered before
    the panel configuration can be applied. Making changes to the panel is
    deferred until the horizon autodiscover is completed, configurations are
    applied in alphabetical order of files where it was imported.
    """
    config_dashboards = horizon_config.get('dashboards', [])
    if config_dashboards or horizon_config.get('default_dashboard'):
        logging.warning(
            '"dashboards" and "default_dashboard" in (local_)settings is '
            'DEPRECATED now and may be unsupported in some future release. '
            'The preferred way to specify the order of dashboards and the '
            'default dashboard is the pluggable dashboard mechanism (in %s).',
            ', '.join([os.path.abspath(module.__path__[0])
                       for module in modules])
        )

    enabled_dashboards = []
    disabled_dashboards = []
    exceptions = horizon_config.get('exceptions', {})
    apps = []
    angular_modules = []
    js_files = []
    js_spec_files = []
    scss_files = []
    panel_customization = []
    update_horizon_config = {}
    for key, config in import_dashboard_config(modules):
        if config.get('DISABLED', False):
            if config.get('DASHBOARD'):
                disabled_dashboards.append(config.get('DASHBOARD'))
            continue

        _apps = config.get('ADD_INSTALLED_APPS', [])
        apps.extend(_apps)

        if config.get('AUTO_DISCOVER_STATIC_FILES', False):
            for _app in _apps:
                module = import_module(_app)
                base_path = os.path.join(module.__path__[0], 'static/')
                file_discovery.populate_horizon_config(horizon_config,
                                                       base_path)

        add_exceptions = six.iteritems(config.get('ADD_EXCEPTIONS', {}))
        for category, exc_list in add_exceptions:
            exceptions[category] = tuple(set(exceptions.get(category, ())
                                             + exc_list))

        angular_modules.extend(config.get('ADD_ANGULAR_MODULES', []))
        # avoid pulling in dashboard javascript dependencies multiple times
        existing = set(js_files)
        js_files.extend([f for f in config.get('ADD_JS_FILES', [])
                         if f not in existing])
        js_spec_files.extend(config.get('ADD_JS_SPEC_FILES', []))
        scss_files.extend(config.get('ADD_SCSS_FILES', []))
        update_horizon_config.update(
            config.get('UPDATE_HORIZON_CONFIG', {}))
        if config.get('DASHBOARD'):
            dashboard = key
            enabled_dashboards.append(dashboard)
            if config.get('DEFAULT', False):
                horizon_config['default_dashboard'] = dashboard
        elif config.get('PANEL') or config.get('PANEL_GROUP'):
            config.pop("__builtins__", None)
            panel_customization.append(config)
    # Preserve the dashboard order specified in settings
    dashboards = ([d for d in config_dashboards
                   if d not in disabled_dashboards] +
                  [d for d in enabled_dashboards
                   if d not in config_dashboards])

    horizon_config['panel_customization'] = panel_customization
    horizon_config['dashboards'] = tuple(dashboards)
    horizon_config.setdefault('exceptions', {}).update(exceptions)
    horizon_config.update(update_horizon_config)
    horizon_config.setdefault('angular_modules', []).extend(angular_modules)
    horizon_config.setdefault('js_files', []).extend(js_files)
    horizon_config.setdefault('js_spec_files', []).extend(js_spec_files)
    horizon_config.setdefault('scss_files', []).extend(scss_files)

    # apps contains reference to applications declared in the enabled folder
    # basically a list of applications that are internal and external plugins
    # installed_apps contains reference to applications declared in settings
    # such as django.contribe.*, django_pyscss, compressor, horizon, etc...
    # for translation, we are only interested in the list of external plugins
    # so we save the reference to it before we append to installed_apps
    horizon_config.setdefault('plugins', []).extend(apps)
    installed_apps[0:0] = apps


# Order matters, list the xstatic module name and the entry point file(s) for
# that module (this is often defined as the "main" in bower.json, and
# as the xstatic module MAIN variable in the very few compliant xstatic
# modules). If the xstatic module does define a MAIN then set the files
# list to None.
# This list is to be used as the base list which is potentially added to in
# local_settings.py before being passed to get_xstatic_dirs()
BASE_XSTATIC_MODULES = [
    ('xstatic.pkg.jquery', ['jquery.js']),
    ('xstatic.pkg.jquery_migrate', ['jquery-migrate.js']),
    ('xstatic.pkg.angular', [
        'angular.js',
        'angular-cookies.js',
        'angular-sanitize.js',
        'angular-route.js'
    ]),
    ('xstatic.pkg.angular_bootstrap', ['angular-bootstrap.js']),
    ('xstatic.pkg.angular_gettext', ['angular-gettext.js']),
    ('xstatic.pkg.angular_lrdragndrop', None),
    ('xstatic.pkg.angular_smart_table', None),
    ('xstatic.pkg.angular_fileupload', ['ng-file-upload-all.js']),
    ('xstatic.pkg.d3', ['d3.js']),
    ('xstatic.pkg.jquery_quicksearch', ['jquery.quicksearch.js']),
    ('xstatic.pkg.jquery_tablesorter', ['jquery.tablesorter.js']),
    ('xstatic.pkg.spin', ['spin.js', 'spin.jquery.js']),
    ('xstatic.pkg.jquery_ui', ['jquery-ui.js']),
    ('xstatic.pkg.bootstrap_scss', ['js/bootstrap.js']),
    ('xstatic.pkg.bootstrap_datepicker', ['bootstrap-datepicker.js']),
    ('xstatic.pkg.hogan', ['hogan.js']),
    ('xstatic.pkg.rickshaw', ['rickshaw.js']),
    ('xstatic.pkg.jsencrypt', ['jsencrypt.js']),
    ('xstatic.pkg.objectpath', ['ObjectPath.js']),
    ('xstatic.pkg.tv4', ['tv4.js']),
    ('xstatic.pkg.angular_schema_form', ['schema-form.js']),

    # @imported in scss files diectly
    ('xstatic.pkg.font_awesome', []),
    ('xstatic.pkg.bootswatch', []),
    ('xstatic.pkg.roboto_fontface', []),
    ('xstatic.pkg.mdi', []),

    # testing only, not included in application
    ('xstatic.pkg.jasmine', []),
    ('xstatic.pkg.termjs', []),
]


def get_xstatic_dirs(XSTATIC_MODULES, HORIZON_CONFIG):
    """Discover static file configuration of the xstatic modules.

    For each entry in the XSTATIC_MODULES list we determine the entry
    point files (which may come from the xstatic MAIN var) and then
    determine where in the Django static tree the xstatic package's contents
    should be placed.

    For jquery.bootstrap.wizard.js the module name is None the static file is
    actually a 3rd-party file but resides in the Horizon source tree and not
    an xstatic package.

    The xstatic.pkg.jquery_ui package had its contents moved by packagers so
    it must be handled as a special case.
    """
    STATICFILES_DIRS = []
    HORIZON_CONFIG['xstatic_lib_files'] = []
    for module_name, files in XSTATIC_MODULES:
        module = import_module(module_name)
        if module_name == 'xstatic.pkg.jquery_ui':
            # determine the correct path for jquery-ui which packagers moved
            if module.VERSION.startswith('1.10.'):
                # The 1.10.x versions already contain 'ui' directory.
                files = ['ui/' + files[0]]

        STATICFILES_DIRS.append(
            ('horizon/lib/' + module.NAME, module.BASE_DIR)
        )

        # pull the file entry points from the xstatic package MAIN if possible
        if hasattr(module, 'MAIN'):
            files = module.MAIN
            if not isinstance(files, list):
                files = [files]

            # just the Javascript files, please (don't <script> css, etc
            # which is explicitly included in style/themes as appropriate)
            files = [file for file in files if file.endswith('.js')]

        # add to the list of files to link in the HTML
        for file in files:
            file = 'horizon/lib/' + module.NAME + '/' + file
            HORIZON_CONFIG['xstatic_lib_files'].append(file)

    return STATICFILES_DIRS


def find_static_files(
        HORIZON_CONFIG,
        AVAILABLE_THEMES,
        THEME_COLLECTION_DIR,
        ROOT_PATH):
    import horizon
    import openstack_dashboard

    os_dashboard_home_dir = openstack_dashboard.__path__[0]
    horizon_home_dir = horizon.__path__[0]

    # note the path must end in a '/' or the resultant file paths will have a
    # leading "/"
    file_discovery.populate_horizon_config(
        HORIZON_CONFIG,
        os.path.join(horizon_home_dir, 'static/')
    )

    # filter out non-angular javascript code and lib
    HORIZON_CONFIG['js_files'] = ([f for f in HORIZON_CONFIG['js_files']
                                   if not f.startswith('horizon/')])

    # note the path must end in a '/' or the resultant file paths will have a
    # leading "/"
    file_discovery.populate_horizon_config(
        HORIZON_CONFIG,
        os.path.join(os_dashboard_home_dir, 'static/'),
        sub_path='app/'
    )

    # Discover theme static resources, and in particular any
    # static HTML (client-side) that the theme overrides
    theme_static_files = {}
    theme_info = theme_settings.get_theme_static_dirs(
        AVAILABLE_THEMES,
        THEME_COLLECTION_DIR,
        ROOT_PATH)

    for url, path in theme_info:
        discovered_files = {}

        # discover static files provided by the theme
        file_discovery.populate_horizon_config(
            discovered_files,
            path
        )

        # Get the theme name from the theme url
        theme_name = url.split('/')[-1]

        # build a dictionary of this theme's static HTML templates.
        # For each overridden template, strip off the '/templates/' part of the
        # theme filename then use that name as the key, and the location in the
        # theme directory as the value. This allows the quick lookup of
        # theme path for any file overridden by a theme template
        template_overrides = {}
        for theme_file in discovered_files['external_templates']:
            # Example:
            #   external_templates_dict[
            #       'framework/widgets/help-panel/help-panel.html'
            #   ] = 'themes/material/templates/framework/widgets/\
            #        help-panel/help-panel.html'
            (templates_part, override_path) = theme_file.split('/templates/')
            template_overrides[override_path] = 'themes/' + \
                                                theme_name + theme_file

        discovered_files['template_overrides'] = template_overrides

        # Save all of the discovered file info for this theme in our
        # 'theme_files' object using the theme name as the key
        theme_static_files[theme_name] = discovered_files

    # Add the theme file info to the horizon config for use by template tags
    HORIZON_CONFIG['theme_static_files'] = theme_static_files
