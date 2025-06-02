import random
import time

from locust import HttpUser, between, task


class ChatUser(HttpUser):
    wait_time = between(5, 20)

    @task
    def ask_question(self):
        self.client.get(
            "/",
            name="home",
        )
        time.sleep(self.wait_time())
        first_question = random.choice(
            [
                "What are the key requirements for this process?",
                "How do I get started with this workflow?",
                "What are the best practices for this task?",
                "What training do I need for this role?",
            ]
        )

        response = self.client.post(
            "/chat",
            name="initial chat",
            json={
                "messages": [
                    {
                        "content": first_question,
                        "role": "user",
                    },
                ],
                "context": {
                    "overrides": {
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "semantic_captions": False,
                        "top": 3,
                        "suggest_followup_questions": True,
                    },
                },
            },
        )
        time.sleep(self.wait_time())
        # use one of the follow up questions.
        follow_up_question = random.choice(response.json()["context"]["followup_questions"])
        result_message = response.json()["message"]["content"]

        self.client.post(
            "/chat",
            name="follow up chat",
            json={
                "messages": [
                    {"content": first_question, "role": "user"},
                    {
                        "content": result_message,
                        "role": "assistant",
                    },
                    {"content": follow_up_question, "role": "user"},
                ],
                "context": {
                    "overrides": {
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "semantic_captions": False,
                        "top": 3,
                        "suggest_followup_questions": False,
                    },
                },
            },
        )


class ChatVisionUser(HttpUser):
    wait_time = between(5, 20)

    @task
    def ask_question(self):
        self.client.get("/")
        time.sleep(self.wait_time())
        self.client.post(
            "/chat/stream",
            json={
                "messages": [
                    {
                        "content": "What patterns can you identify in this visual data?",
                        "role": "user",
                    }
                ],
                "context": {
                    "overrides": {
                        "top": 3,
                        "temperature": 0.3,
                        "minimum_reranker_score": 0,
                        "minimum_search_score": 0,
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "semantic_captions": False,
                        "suggest_followup_questions": False,
                        "use_oid_security_filter": False,
                        "use_groups_security_filter": False,
                        "vector_fields": "textAndImageEmbeddings",
                        "use_gpt4v": True,
                        "gpt4v_input": "textAndImages",
                    }
                },
                "session_state": None,
            },
        )
        time.sleep(self.wait_time())
        self.client.post(
            "/chat/stream",
            json={
                "messages": [
                    {"content": "Compare the trends shown in these charts and graphs.", "role": "user"}
                ],
                "context": {
                    "overrides": {
                        "top": 3,
                        "temperature": 0.3,
                        "minimum_reranker_score": 0,
                        "minimum_search_score": 0,
                        "retrieval_mode": "hybrid",
                        "semantic_ranker": True,
                        "semantic_captions": False,
                        "suggest_followup_questions": False,
                        "use_oid_security_filter": False,
                        "use_groups_security_filter": False,
                        "vector_fields": "textAndImageEmbeddings",
                        "use_gpt4v": True,
                        "gpt4v_input": "textAndImages",
                    }
                },
                "session_state": None,
            },
        )
