from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

#é um modelo que vai  representar uma tabela no BD
Base = declarative_base()


class Coleta(Base):
    __tablename__ = 'coletas'

    id = Column(Integer, primary_key=True)
    nome = Column(String)
    senha = Column(String)


    def __repr__(self):
        return f"<Coleta(id='{self.id}', nome='{self.nome}')>"