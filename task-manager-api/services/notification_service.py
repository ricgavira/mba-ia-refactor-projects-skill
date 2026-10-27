import logging
import smtplib

from utils.helpers import utc_now

logger = logging.getLogger(__name__)


class NotificationService:
    """Notificações por e-mail. A configuração SMTP é injetada (vem de config/settings.py)."""

    def __init__(self, host, port, user, password):
        self.email_host = host
        self.email_port = port
        self.email_user = user
        self.email_password = password
        self.notifications = []

    @classmethod
    def from_config(cls, config):
        return cls(config['EMAIL_HOST'], config['EMAIL_PORT'], config['EMAIL_USER'], config['EMAIL_PASSWORD'])

    def send_email(self, to, subject, body):
        if not self.email_user:
            logger.warning('SMTP não configurado; e-mail para %s não enviado', to)
            return False
        try:
            server = smtplib.SMTP(self.email_host, self.email_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, to, f'Subject: {subject}\n\n{body}')
            server.quit()
            logger.info('Email enviado para %s', to)
            return True
        except smtplib.SMTPException as exc:
            logger.error('Erro ao enviar email: %s', exc)
            return False

    def notify_task_assigned(self, user, task):
        subject = f'Nova task atribuída: {task.title}'
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f'Prioridade: {task.priority}\nStatus: {task.status}')
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utc_now(),
        })

    def notify_task_overdue(self, user, task):
        subject = f'Task atrasada: {task.title}'
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
