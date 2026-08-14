from central_load_plan.extension import db
from central_load_plan.models import JobType

from wtforms_sqlalchemy.orm import model_form

JobTypeForm = model_form(JobType, db_session=db.session)
