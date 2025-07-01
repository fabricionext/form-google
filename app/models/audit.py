"""
Modelos para Auditoria e Notificações.
"""
import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import BaseModel

class AuditAction(enum.Enum):
    """Enum para ações de auditoria."""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SYNC = "SYNC"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ACCESS = "ACCESS"
    IMPORT = "IMPORT"

class NotificationType(enum.Enum):
    """Enum para tipos de notificação."""
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

class AuditLog(BaseModel):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True) # Pode ser nulo para ações do sistema
    action = Column(Enum(AuditAction), nullable=False)
    target_type = Column(String(100))
    target_id = Column(String(255))
    details = Column(Text)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AuditLog(user_id={self.user_id}, action='{self.action}', target='{self.target_type}:{self.target_id}')>"

class Notification(BaseModel):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('clients.id'), nullable=False) # Assumindo que notificamos 'clients'
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, nullable=False)
    notification_type = Column(Enum(NotificationType), default=NotificationType.INFO, nullable=False)
    related_object_type = Column(String(100))
    related_object_id = Column(String(255))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("Client")

    def __repr__(self):
        return f"<Notification(user_id={self.user_id}, message='{self.message[:20]}...', read={self.read})>" 