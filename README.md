# deployctl
## Sources
- [Installing Docker Engine](https://docs.docker.com/engine/)

> [!TIP]
> Install this using Homebrew: `brew tap ayaans16/deployctl https://github.com/ayaans16/deployctl`

## How It Works
`deployctl` is a command-line interface tool that allows you to automate the deployment of your projects with little to no extra work, just providing the tool some information so it can do the heavy lifting for you.

All the work is done using two files: the standard `.env` file and a special `deployctl.conf` file in your project's root.
> [!TIP]
> You can add `deployctl.conf` into `.gitignore` if you want to hide any specifics.
---
## `deployctl.conf`
```yaml
  core {
      project_name = "name"
      email_address = "your@email.com"

      setup_command = "python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"

      start_command = "gunicorn --workers=4 --bind=0.0.0.0:8000 myapp:app"
      
      how_to_run = "docker" # only put docker or linux here

      path_for_project = "~/apps/"

      # port your app listens on inside the container (used for docker run -p PORT:PORT)
      # this should match whatever port your nginx config's proxy_pass points at
      port = 3000
  }

  lint {
      # this is the path to the folder with your unit tests
      unit_test_folder = "/path/to/tests"

      # this is the command used to run the unit tests
      # must be defined for the language you're using
      unit_test_command = "pytest"
  }

  web {
      nginx_config_filename = "nginx.conf"
      domain = "domain.com"
  }
```
- [x] Add your name and email
- [x] Add your setup and startup command
> [!WARNING]
> These are not the same. Setup will set up the environment like installing dependencies and startup will actually run your command.
- [x] Choose if you wish to Dockerize the project or want to run it in a GNU screen
- [x] Add the absolute path to your project from the root of your device/VPS
- [x] Add a port for Docker and Nginx reverse proxying
> [!IMPORTANT]
> Choosing to run your project in Docker requires you to have a Dockerfile in your project's root.
- Add your unit test folder path and unit test command
- Add the Nginx configuration filename located in root with your domain name so it can create the reverse proxy
---
## `.env`
```yaml
  # vps information
  VPS_IP=
  VPS_USER=

  # use VPS_PASSWORD for password auth, or VPS_SSH_KEY_PATH for key-based auth
  # (required for AWS EC2, which is key-only by default), set one, not both
  VPS_PASSWORD=
  VPS_SSH_KEY_PATH=
```
- Add your VPS informartion
- Add **either** the password for your VPS or the path to your private key file to access the VPS via SSH.
---
## Commands
| Command | Purpose |
| -------- | -------- |
| `deployctl deploy` | Runs the whole pipeline |
| `deployctl lint` | Only runs the unit testing |
| `deployctl sync` | Pushes local files to your VPS |
| `deployctl run` | Starts the GNU screen or Docker |
| `deployctl health` | Health check and responsiveness on its port |
| `deployctl nginx` | Pushes the Nginx config and reloads |
| `deployctl ssl` | Runs pipeline to install certbot and generate an SSL certificate |
| `deployctl rollback` | Rolls back to the previously deployed version |