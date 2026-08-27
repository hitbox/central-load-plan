from .email_from_template_job_template import EmailFromTemplateJobTemplate
from .file_output_from_template_job_template import FileOutputFromTemplateJobTemplate
from .json_output_job_template import JSONOutputJobTemplate
from .move_file_job_template import MoveFileJobTemplate
from .polybase import JobTemplate
from .send_to_template import SendToTemplate

_classes = [
    EmailFromTemplateJobTemplate,
    FileOutputFromTemplateJobTemplate,
    JSONOutputJobTemplate,
    MoveFileJobTemplate,
    JobTemplate,
    SendToTemplate,
]

for class_ in _classes:
    if 'make_job' not in class_.__dict__:
        raise TypeError(f'Must implement `make_job` for {class_}')
