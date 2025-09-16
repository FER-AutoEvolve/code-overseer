import argparse
import datetime
import json
import logging
import os

from api_server import ApiServer
from core import Result, Unit
from code_overseeing import CodeOverseer
from configuration import Configuration
from prompting.openai import PromptManager

def main(configuration_file_path: str) -> Result[Unit]:
    logging.info(f"Program starting with configuration file path: {configuration_file_path}")

    # Load the configuration file
    config: Configuration = None
    with open(configuration_file_path, "r") as config_file:
        config_json = json.load(config_file)
        config_res = Configuration.from_dict(config_json)
        if config_res.is_err():
            logging.error(f"Failed to load configuration")
            return Result.err("Failed to load configuration")
        config = config_res.unwrap()

    logging.info(f"Configuration file loaded successfully")

    # Setup prompt manager
    res_llm_openai_config = config.get_llm_openai_config()
    if res_llm_openai_config.is_err():
        logging.error(f"Failed to get OpenAI LLM configuration: {res_llm_openai_config.message}")
        return Result.err(res_llm_openai_config.message)
    llm_openai_config = res_llm_openai_config.unwrap()
    
    prompt_manager = PromptManager(llm_openai_config, logging.getLogger())

    # Set up the code overseer
    code_overseer = CodeOverseer(config.code_overseer_config, prompt_manager, logging.getLogger())

    # start the Fast API server
    server = ApiServer(config.fast_api_config, code_overseer, logging.getLogger())
    res_server_start = server.start_server()
    if res_server_start.is_err():
        logging.error(f"Error starting the FastAPI server: {res_server_start.message}")
        return Result.err(res_server_start.message)
    logging.info(f"FastAPI server started successfully")


    logging.info(f"Program ended successfully")
    return Result.ok(Unit())

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--config', help='Path to the configuration file', default='configuration.json')
    argparser.add_argument('--log-to-file', help='Log to file', action='store_true')

    args = argparser.parse_args()

    # Set up logging
    # Log to console
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s.%(msecs)03d| %(message)s', datefmt='%d.%m.%yT%H:%M:%S')

    # Log to file if the flag is set
    if args.log_to_file:
        cwd = os.getcwd()
        logging_dir_path = os.path.join(cwd, "logs")
        # Create the logs directory if it doesn't exist
        os.makedirs(logging_dir_path, exist_ok=True)
        logging_file_path = os.path.join(logging_dir_path, datetime.datetime.now().strftime("%y_%m_%dT%H_%M_%S")) + ".log"

        # Create a file handler
        file_handler = logging.FileHandler(logging_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s.%(msecs)03d| %(message)s', datefmt='%d.%m.%yT%H:%M:%S'))

        # Add the file handler to the root logger
        logging.getLogger().addHandler(file_handler)
    
    main(args.config)