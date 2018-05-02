import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import create_engine
from sqlalchemy import DateTime
import datetime

Base = declarative_base()

class Categories(Base): 
    __tablename__ = 'categories' 

    id = Column(Integer, primary_key=True) 
    name = Column(String(250), nullable=False) 

    @property 
    def serialize(self): 
        return { 
            'id': self.id, 
            'name': self.name, 
            'description': self.description
        }   

class Items(Base): 
    __tablename__ = 'items' 

    name = Column(String(80), nullable = False) 
    id = Column(Integer, primary_key = True) 
    description = Column(String(500)) 
    price = Column(String(8))
    image = Column(String(250))
    time_created = Column('last_updated', DateTime(timezone=True), server_default=func.now())
    category_id = Column(Integer, ForeignKey('categories.id'))
    categories = relationship(Categories)

engine = create_engine('sqlite:///catalog.db') 
Base.metadata.create_all(engine)
