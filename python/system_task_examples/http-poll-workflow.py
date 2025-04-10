from conductor.client.configuration.configuration import Configuration
from conductor.client.workflow.executor.workflow_executor import WorkflowExecutor
from conductor.client.workflow.conductor_workflow import ConductorWorkflow
from conductor.client.automator.task_handler import TaskHandler
from conductor.client.workflow.task.http_poll_task import HttpPollTask, HttpPollInput
from conductor.client.workflow.task.set_variable_task import SetVariableTask
from conductor.client.workflow.task.switch_task import SwitchTask

def register_workflow(workflow_executor: WorkflowExecutor) -> ConductorWorkflow:
    # 1) Define the HTTP Poll input
    http_poll_input = HttpPollInput(
        uri="https://httpbin.org/delay/10",  # The API URL to poll for status
        method="GET",  # HTTP method (GET)
        accept="application/json",  # Accept header for JSON response
        termination_condition='$.output.response.statusCode == 200',  # Condition to stop polling
        polling_interval=10  # Poll every 60 seconds
    )

    # 2) Define the HTTP Poll task for checking the file processing status
    http_poll_task = HttpPollTask(
        task_ref_name="check_file_processing_status",  # Reference name for the task
        http_input=http_poll_input  # Pass the HTTP Poll input
    )

    # 3) Define SetVariableTask for success case
    set_processing_complete_variable = SetVariableTask(
        task_ref_name="set_processing_complete_variable"
    )
    set_processing_complete_variable.input_parameters.update({
        'processing_status': 'COMPLETED'  # Set the status to completed
    })

    # Define SetVariableTask for failure case
    set_processing_failed_variable = SetVariableTask(
        task_ref_name="set_processing_failed_variable"
    )
    set_processing_failed_variable.input_parameters.update({
        'processing_status': 'FAILED'  # Set the status to failed
    })

    # 4) Define SwitchTask to handle success and failure cases
    switch_task = SwitchTask(
        task_ref_name="check_processing_status",  # Reference name for the switch task
        case_expression="${check_file_processing_status.output.response.statusCode}",  # Case expression based on status
        use_javascript=False  # Use value-param evaluator type
    )

    # Configure the decision cases for the SwitchTask
    switch_task.switch_case(200, set_processing_complete_variable)  # Case for success (file processed)
    switch_task.default_case(set_processing_failed_variable)  # Default case for any other status

    # Define the workflow and add the tasks
    workflow = ConductorWorkflow(
        name="file_processing_workflow",
        executor=workflow_executor
    )
    workflow.version = 1
    workflow.add(http_poll_task)  # Add the HTTP Poll task to check file processing status
    workflow.add(switch_task)  # Add the switch task to handle the result

    # Register the workflow
    workflow.register(True)

    return workflow


def main():
    # Initialize Configuration (API configuration)
    api_config = Configuration()

    # Initialize Workflow Executor
    workflow_executor = WorkflowExecutor(configuration=api_config)

    # Register the workflow
    workflow = register_workflow(workflow_executor)

    # Starting the worker polling mechanism
    task_handler = TaskHandler(configuration=api_config)
    task_handler.start_processes()

    # Input for the workflow
    workflow_input = {
        "file_id": "FILE-00123",
        "auth_token": "your_authorization_token"
    }

    # Start workflow execution
    workflow_run = workflow_executor.execute(
        name=workflow.name,
        version=workflow.version,
        workflow_input=workflow_input
    )

    print(f"Started workflow ID: {workflow_run.workflow_id}")
    print(f"View in UI: {api_config.ui_host}/execution/{workflow_run.workflow_id}")

    # Stop task handler after execution
    task_handler.stop_processes()


if __name__ == '__main__':
    main()
