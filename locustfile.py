from locust import HttpUser, task, between


class ChatUser(HttpUser):
    wait_time = between(0.5, 1.5)

    @task
    def send_message(self):
        self.client.post("/chat/locust", json={"message": "hello"})
