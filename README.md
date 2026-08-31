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

3. Prepare python venv and install requiremets in it:

    `python -m venv env`

    `./env/Scripts/activate`

    `pip install -r ./requirements.txt`

4. Reset the codebase directory by running `python ./reset_codebase.py`.

## Experiment notifications
You can configure an experiment-only notification channel that sends data to an external tracker component.

Configuration section:
```
"ExperimentNotification": {
    "Enabled": true,
    "Endpoint": "http://experiment-director:8002/notify",
    "ComponentName": "Code Overseer"
}
```

Usage from code:
```
from experiment_notification import ExperimentEventTypes

logger.experiment(
    "Build iteration finished",
    event_type=ExperimentEventTypes.SUCCESS
)
```

Payload contains component name, event timestamp, event message, and event type (`Failure` / `Success` / `Info`).
This pathway is exclusive and does not write to ordinary logging handlers (console/file).

## Prompting providers

Set `Prompting.Provider` to `openai` to use any OpenAI model. This provider requires a non-empty `Prompting.ProviderConfig.Model` value, for example `gpt-4.1-mini`. The existing `openai_gpt_4_1` and `openai_gpt_5` providers remain available and keep their pinned models.

## Run in docker
> This container is intended to be run as part of a docker compose and not specifically as a standalone container

The Dockerfile contains two stages. The `base` stage only starts the code-overseer instance and points it to an existing codebase; this codebase is planned to be in a volume. The `with_codebase` stage copies a codebase in the `./codebase` directory to the container. The `with_codebase` stage doesn't complie or start the codebase.

1. Build the Docker image: 

    `docker build -t code-overseer --build-args PORT=3000 .`

2. Run the Docker container:

    `docker run -d --name code-overseer -p 3000:3000 code-overseer`
