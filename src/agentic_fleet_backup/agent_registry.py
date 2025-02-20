import os

from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import MagenticOneGroupChat, SelectorGroupChat
from autogen_ext.agents.file_surfer import FileSurfer
from autogen_ext.agents.magentic_one import MagenticOneCoderAgent
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor


def initialize_default_agents(app_manager, config_manager, user_session, defaults, env_config):
    """
    Initialize and return a dictionary of default agents:
      - websurfer: instance of MultimodalWebSurfer
      - filesurfer: instance of FileSurfer
      - coder: instance of MagenticOneCoderAgent
      - executor: instance of CodeExecutorAgent
    """
    web_surfer_config = config_manager.get_agent_settings("web_surfer")
    surfer = MultimodalWebSurfer(
        name="WebSurfer",
        model_client=app_manager.model_client,
        description=web_surfer_config["description"],
        downloads_folder=env_config["downloads_dir"],
        debug_dir=env_config["debug_dir"],
        headless=True,
        start_page=user_session.get("start_page", defaults.get("start_page")),
        animate_actions=False,
        to_save_screenshots=True,
        use_ocr=False,
        to_resize_viewport=True
    )

    file_surfer_config = config_manager.get_agent_settings("file_surfer")
    file_surfer = FileSurfer(
        name="FileSurfer",
        model_client=app_manager.model_client,
        description=file_surfer_config["description"]
    )

    coder = MagenticOneCoderAgent(
        name="Coder",
        model_client=app_manager.model_client
    )

    workspace_dir = os.path.join(os.getcwd(), env_config["workspace_dir"])
    executor_settings = config_manager.get_agent_settings("executor")
    code_executor = LocalCommandLineCodeExecutor(
        work_dir=workspace_dir,
        timeout=executor_settings["config"]["timeout"]
    )

    executor = CodeExecutorAgent(
        name="Executor",
        code_executor=code_executor,
        description=executor_settings["description"]
    )

    return {
        "websurfer": surfer,
        "filesurfer": file_surfer,
        "coder": coder,
        "executor": executor
    }


def initialize_agent_team(app_manager, user_session, team_config, default_agents, defaults):
    """
    Initialize and return an agent team based on the active profile.
    If active_profile is 'MagenticFleet One', then use MagenticOneGroupChat with the default agents.
    Otherwise, use SelectorGroupChat with agents selected from team_config participants.
    """
    active_profile = user_session.get("active_chat_profile", "MagenticFleet One")
    model_client = app_manager.model_client
    if active_profile == "MagenticFleet One":
        team = MagenticOneGroupChat(
            model_client=model_client,
            participants=[
                default_agents["websurfer"],
                default_agents["filesurfer"],
                default_agents["coder"],
                default_agents["executor"]
            ],
            max_turns=user_session.get("max_rounds", defaults.get("max_rounds", 10)),
            max_stalls=user_session.get("max_stalls", defaults.get("max_stalls", 3))
        )
    else:
        participants = []
        for agent_name in team_config.get("participants", []):
            key = agent_name.lower()
            if key in default_agents:
                participants.append(default_agents[key])
        team = SelectorGroupChat(
            agents=participants,
            model_client=model_client,
            termination_conditions=[
                MaxMessageTermination(max_messages=team_config["config"]["max_messages"]),
                TextMentionTermination(text="DONE", ignore_case=True)
            ],
            selector_description=team_config["config"]["selector_description"]
        )
    return team
