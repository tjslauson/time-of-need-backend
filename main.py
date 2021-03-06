import datetime
import os
import shutil
from subprocess import call

from flask.ext.script import Manager, Server

from ton import config, models
from ton.application import app

manager = Manager(app)
server = Server(
    use_debugger=True,
    use_reloader=True,
    host='0.0.0.0',
    port='8000'
)


@manager.command
def initialize_db():
    # Move existing SQLite database out of the way
    if os.path.isfile(config.DATABASE_PATH):
        ext = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        new_path = "{path}.{ext}".format(path=config.DATABASE_PATH, ext=ext)
        shutil.move(config.DATABASE_PATH, new_path)

    # Flush the database
    app.db.drop_all()
    app.db.create_all()

    # Add roles
    admin_role = models.Role(name='Administrator')
    app.db.session.add(admin_role)
    standard_role = models.Role(name='Standard')
    app.db.session.add(standard_role)
    admin = models.User(
        username='admin',
        email='admin@example.com',
        password='supersecret',
        roles=[admin_role],
        active=True)
    app.db.session.add(admin)

    # Days of week
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
                "Saturday", "Sunday"]:
        app.db.session.add(models.DayOfWeek(day=day))

    # Services
    services = [
        "Shelter", "Food", "Clothing Closets / Assistance Programs",
        "Shower Facilities", "Support Groups", "Medical Facilities",
        "Employment Assistance", "Transportation Assistance",
        "Suicide Prevention", "Domestic Violence Resources",
        "Veteran Services", "Referral Services"
    ]
    for s in services:
        app.db.session.add(models.Service(name=s))

    # Save
    app.db.session.commit()

manager.add_command('runserver', server)


@manager.command
def generate_erd():
    """
    Generate UML that represents an ERD

    Command wrapper for sadisplay. Must have graphviz installed.
    See https://bitbucket.org/estin/sadisplay/wiki/Home
    """
    import sadisplay
    from ton import models

    desc = sadisplay.describe([getattr(models, attr) for attr in dir(models)])
    with open('schema.dot', 'w') as f:
        f.write(sadisplay.dot(desc))
    ret = call("dot -Tpng schema.dot > schema.png", shell=True)
    if ret == 0:
        os.remove("schema.dot")


if __name__ == '__main__':
    manager.run()
