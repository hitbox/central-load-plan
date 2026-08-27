"""
Job subclasses that `do_work`.
"""
from .email_from_template_job import EmailFromTemplateJob
from .file_output_from_template_job import FileOutputFromTemplateJob
from .job_type import JobType
from .job_type import JobTypeEnum
from .json_output_job import JSONOutputJob
from .move_file_job import MoveFileJob
from .polybase import Job
from .send_to import SendTo

_classes = [
    EmailFromTemplateJob,
    FileOutputFromTemplateJob,
    #JobType, # Not a job class
    #JobTypeEnum, # ...
    #SendTo, # ...
    JSONOutputJob,
    MoveFileJob,
    Job,
]

# Raise for missing methods
for class_ in _classes:
    if 'do_work' not in class_.__dict__:
        raise TypeError(f'Must implement `do_work` for {class_}')
