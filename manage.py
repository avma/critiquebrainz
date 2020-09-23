﻿import os
import subprocess
from werkzeug.serving import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from brainzutils import cache
import click
from critiquebrainz import frontend, ws
from critiquebrainz.data import dump_manager
import critiquebrainz.data.utils as data_utils
import critiquebrainz.data.fixtures as _fixtures


cli = click.Group()

application = DispatcherMiddleware(frontend.create_app(), {
    "/ws/1": ws.create_app()
})

# Files listed here will be monitored for changes in debug mode and will
# force a reload when modified.
OBSERVE_FILES = [
    "critiquebrainz/frontend/static/build/manifest.json",
]


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", show_default=True)
@click.option("--port", "-p", default=8080, show_default=True)
@click.option("--debug", "-d", is_flag=True,
              help="Turns debugging mode on or off. If specified, overrides "
                   "'DEBUG' value in the config file.")
def runserver(host, port, debug=False):
    run_simple(
        hostname=host,
        port=port,
        application=application,
        use_debugger=debug,
        extra_files=OBSERVE_FILES,
        use_reloader=debug,
    )


@cli.command()
def extract_strings():
    """Extract all strings into messages.pot.

    This command should be run after any translatable strings are updated.
    Otherwise updates are not going to be available on Transifex.
    """
    _run_command("pybabel extract -F critiquebrainz/frontend/babel.cfg -k lazy_gettext "
                 "-o critiquebrainz/frontend/messages.pot critiquebrainz/frontend")
    click.echo("Strings have been successfully extracted into messages.pot file.")


@cli.command()
def pull_translations():
    """Pull translations for languages defined in config from Transifex and compile them.

    Before using this command make sure that you properly configured Transifex client.
    More info about that is available at http://docs.transifex.com/developer/client/setup#configuration.
    """
    languages = ','.join(frontend.create_app().config['SUPPORTED_LANGUAGES'])
    _run_command("tx pull -f -r critiquebrainz.critiquebrainz -l %s" % languages)


@cli.command()
def update_strings():
    """Extract strings and pull translations from Transifex."""
    extract_strings()
    pull_translations()


@cli.command()
def compile_translations():
    """Compile translations for use."""
    _run_command("pybabel compile -d critiquebrainz/frontend/translations")
    click.echo("Translated strings have been compiled and ready to be used.")


@cli.command()
def clear_memcached():
    with frontend.create_app().app_context():
        cache.flush_all()
    click.echo("Flushed everything from memcached.")


@click.option("--skip-create-db", "-s", is_flag=True,
              help="Skip database creation step.")
@click.option("--test-db", "-t", is_flag=True,
              help="Initialize the test database.")
@click.option("--force", "-f", is_flag=True,
              help="Drop existing tables and types.")
@cli.command()
def init_db(skip_create_db=False, test_db=False, force=False):
    """Initialize the database.

    * Creates the database.
    * Creates all tables.
    * Adds fixtures required to run the app.
    """
    click.echo("Initializing the database...")

    if force:
        click.echo("Dropping existing tables and types...")
        data_utils.drop_tables()
        data_utils.drop_types()
        click.echo("Done!")

    if test_db:
        db_uri = frontend.create_app(config_path=os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'critiquebrainz', 'test_config.py'
        )).config['SQLALCHEMY_DATABASE_URI']
    else:
        db_uri = frontend.create_app().config['SQLALCHEMY_DATABASE_URI']

    if not skip_create_db:
        create_extension(db_uri)

    click.echo("Creating tables... ", nl=False)
    data_utils.create_all()
    click.echo("Done!")

    click.echo("Adding fixtures... ")
    app = frontend.create_app()
    with app.app_context():
        _fixtures.install(*_fixtures.all_data)
    click.echo("Done!")

    click.echo("Initialization has been completed!")


def create_extension(db_uri):
    host, port, db, username, password = data_utils.explode_db_uri(db_uri)
    psql_cmd = "psql -h %s -p %s -U %s -W %s %s" % (host, port, username, password, db)
    exit_code = subprocess.call(
        '%s  -t -A -c "CREATE EXTENSION IF NOT EXISTS \\"%s\\";" %s' %
        (psql_cmd, 'uuid-ossp', db),
        shell=True,
    )
    if exit_code != 0:
        raise Exception('Failed to create PostgreSQL extension!')


def _run_command(command):
    return subprocess.check_call(command, shell=True)


cli.add_command(dump_manager.cli, name="dump")


if __name__ == '__main__':
    cli()
