from autogen_agentchat.messages import TextMessage


class ChatMessage(TextMessage):
    def __init__(self, content: str, source: str, role: str = "user"):
        super().__init__(content=content, source=source)
        self.__dict__["role"] = role
