## openplotter-notifications

OpenPlotter app to manage Signal K notifications

### Installing

Install [openplotter-settings](https://github.com/openplotter/openplotter-settings) for **production**.

#### For production

Install Notifications from openplotter-settings app.

#### For development

Install openplotter-notifications dependencies:

`sudo apt install openplotter-settings openplotter-signalk-installer python3-websocket python3-requests`

Clone the repository:

`git clone https://github.com/openplotter/openplotter-notifications`

Make your changes and create the package:

```
cd openplotter-notifications
dpkg-buildpackage -b
```

Install the package:

```
cd ..
sudo dpkg -i openplotter-notifications_x.x.x-xxx_all.deb
```

Run post-installation script:

`sudo notificationsPostInstall`

Run:

`openplotter-notifications`

Pull request your changes to github and we will check and add them to the next version of the [Debian package](https://cloudsmith.io/~openplotter/repos/openplotter/packages/).

### Documentation

https://openplotter.readthedocs.io

### Support

http://forum.openmarine.net/forumdisplay.php?fid=1