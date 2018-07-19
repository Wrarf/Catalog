from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Category(Base):
    __tablename__ = 'category'

    name = Column(String(32), primary_key=True)


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    category_name = Column(String(32), ForeignKey('category.name'))
    category = relationship(Category)
    name = Column(String(32), nullable=False)
    description = Column(String(250))
    creator_id = Column(Integer, ForeignKey('user.id'))
    creator = relationship(User)

    @property
    def serialize(self):
        return {
            'name': self.name,
            'category_name': self.category_name,
            'description': self.description,
        }


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
