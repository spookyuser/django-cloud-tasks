from unittest.mock import patch, ANY

from gcp_pilot.pubsub import Message
from sample_app.tests.tests_base_tasks import AuthenticationMixin


class SubscriberTaskViewTest(AuthenticationMixin):
    def url(self, name):
        return f"/subscriptions/{name}"

    def trigger_subscriber(self, content, attributes):
        url = "/subscriptions/ParentSubscriberTask"
        message = Message(
            id="i-dont-care",
            data=content,
            attributes=attributes,
            subscription="potato",
        )
        return self.client.post(path=url, data=message.dump(), content_type="application/json")

    def test_propagate_headers(self):
        content = {
            "price": 10,
            "quantity": 42,
        }
        attributes = {
            "HTTP_traceparent": "trace-this-potato",
            "HTTP_another-random-header": "please-do-not-propagate-this",
        }

        with patch("gcp_pilot.tasks.CloudTasks.push") as push:
            with patch("django_cloud_tasks.tasks.TaskMetadata.from_task_obj"):
                self.trigger_subscriber(content=content, attributes=attributes)

        expected_kwargs = {
            "queue_name": "tasks",
            "url": "http://localhost:8080/tasks/CalculatePriceTask",
            "payload": '{"price": 10, "quantity": 42}',
            "headers": {"Traceparent": "trace-this-potato", "X-CloudTasks-Projectname": ANY},
        }
        push.assert_called_once_with(**expected_kwargs)
