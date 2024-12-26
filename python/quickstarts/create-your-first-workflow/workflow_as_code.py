from conductor.client.http.models import StartWorkflowRequest
from conductor.client.configuration.configuration import Configuration
from conductor.client.configuration.settings.authentication_settings import AuthenticationSettings
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.task.simple_task import SimpleTask
from conductor.client.workflow.task.http_task import HttpTask
from conductor.client.workflow.task.switch_task import SwitchTask


def main():
    # Sign up at https://developer.orkescloud.com and create an application.
    # Use your application's Key ID and Key Secret here:
    conf = Configuration(base_url='https://developer.orkescloud.com',
                         authentication_settings=AuthenticationSettings(key_id='_CHANGE_ME_',
                                                                        key_secret='_CHANGE_ME_'))

    # A WorkflowExecutor instance is used to register and execute workflows.
    executor = WorkflowExecutor(conf)

    # Create the workflow definition.
    workflow = ConductorWorkflow(
        executor=executor,
        name='myFirstWorkflow',
        description='Workflow that greets a user. Uses a Switch task, HTTP task, and Simple task.',
        version=1
    )

    # Create the tasks.
    httpTask = HttpTask('get-user_ref', {'uri': 'https://randomuser.me/api/'})
    switchTask = SwitchTask('user-criteria_ref', '${get-user_ref.output.response.body.results[0].location.country}').switch_case(
        'United States', SimpleTask('helloWorld', 'simple_ref').input(
            key='user', value='${get-user_ref.output.response.body.results[0].name.first}'))

    # Add the tasks to the workflow using `add` method or the `>>` operator.
    workflow.add(httpTask)
    workflow >> switchTask

    # Register the workflow.
    workflow.register(True)
    print(f"Registered workflow {workflow.name}")

    # Start the workflow.
    request = StartWorkflowRequest()
    request.name = 'myFirstWorkflow'
    request.version = 1
    id = executor.start_workflow(request)
    print(f"Started workflow {id}")


if __name__ == '__main__':
    main()
