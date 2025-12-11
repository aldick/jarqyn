import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ReportStatus(str, enum.Enum):
    RECEIVED = "received"
    IN_PROCESS = "in_process"
    DONE = "done"


class ReportCategory(str, enum.Enum):
    ROAD_DEFECTS          = "Дефекты дорог и тротуаров"
    LIGHTING              = "Неисправное уличное освещение"
    PLAYGROUNDS           = "Детские и спортивные площадки"
    WASTE                 = "Мусор и отходы"
    ANIMALS               = "Бездомные или мертвые животные"
    TREES                 = "Аварийные деревья и зелёные насаждения"
    OPEN_MANHOLES         = "Открытые люки и засоры ливнёвки"
    VANDALISM             = "Вандализм и граффити"
    ILLEGAL_TRADE         = "Незаконная торговля и реклама"
    SNOW_ICE              = "Сосульки, снег и наледь"
    ECOLOGY               = "Экологические проблемы"
    PUBLIC_TRANSPORT      = "Проблемы с общественным транспортом"
    BIKE_SCOOTER          = "Велодорожки и брошенные самокаты"
    PUBLIC_TOILETS        = "Общественные туалеты"
    PARKING               = "Незаконная парковка"
    OTHER                 = "Другое"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) 
    
    image_url = Column(String, nullable=False)
    original_description = Column(Text, nullable=True) 
    address = Column(String, nullable=True)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    title = Column(String, nullable=True) 
    generated_description = Column(Text, nullable=True) 
    category = Column(Enum(ReportCategory), nullable=True) 
    priority = Column(String, nullable=True)
    
    status = Column(Enum(ReportStatus), default=ReportStatus.RECEIVED)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", backref="reports")
