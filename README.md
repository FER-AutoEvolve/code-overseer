# code-overseer
The code overseer component repository with dockerization. Accepts a strategic code change description and uses it to generate and apply code change commands on a codebase.

## Run in debug
1. Prepare a `configuration.local.json` file from the example structure in `configuration.json`. 
2. Run in VS Code debugger with the following `.vscode/launch.json`:
```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: main.py",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/src/main.py",
            "args": [
                "--config", "${workspaceFolder}/configuration.local.json",
                "--log-to-file"
            ],
            "console": "integratedTerminal"
        }
    ]
}
```

## Run in docker
> This container is intended to be run as part of a docker compose and not specifically as a standalone container

The Dockerfile contains two stages. The `base` stage only starts the code-overseer instance and points it to an existing codebase; this codebase is planned to be in a volume. The `with_codebase` stage copies a codebase in the `./codebase` directory to the container. The `with_codebase` stage doesn't complie or start the codebase.

1. Build the Docker image: 

    `docker build -t code-overseer .`

2. Run the Docker container:

    `docker run -d --name code-overseer -p 3000:3000 code-overseer`
