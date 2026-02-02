"""
Celery tasks package.
"""

from app.tasks.matching_tasks import process_resume_matching

__all__ = ["process_resume_matching"]
