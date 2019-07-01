from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.orm import joinedload, relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sql_helper.caching_query import query_callable, FromCache
from hashlib import md5
from dogpile.cache.region import make_region

Base = declarative_base()


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50))


class Config(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    person = Column(Integer, ForeignKey('person.id'))
    address = Column(String)
    person_ref = relationship(Person)


e = create_engine("sqlite://", echo=True)
Base.metadata.create_all(e)


def md5_key_mangler(key):
    """Receive cache keys as long concatenated strings;
    distill them into an md5 hash.

    """
    return md5(key.encode('ascii')).hexdigest()


regions = {}
regions['default'] = make_region(key_mangler=md5_key_mangler)\
    .configure('dogpile.cache.memory_pickle')

Session = sessionmaker(bind=e, query_cls=query_callable(regions))

sess = Session()
sess.add(Config(person_ref=Person(name='se1')))
sess.add(Config(person_ref=Person(name='man1')))
sess.commit()

# joinedload deactivates lazy loading for person_ref

conf = sess.query(Config).options(joinedload(Config.person_ref), FromCache("default")).first()
sess.commit()
sess.close()

print("_____NO MORE SQL!___________")


conf = sess.query(Config).options(joinedload(Config.person_ref), FromCache("default")).first()
print(conf.person_ref.name)
