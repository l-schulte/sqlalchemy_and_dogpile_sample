from sqlalchemy import Column, String, Integer, ForeignKey, create_engine
from sqlalchemy.orm import joinedload, relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sql_helper.caching_query import query_callable, FromCache, md5_key_mangler
from dogpile.cache.region import make_region

Base = declarative_base()


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)


class Config(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    person = Column(Integer, ForeignKey('person.id'))
    address = Column(String)
    person_ref = relationship(Person)


# Using sqlite and letting sqlalchemy create the tables.

e = create_engine("sqlite://", echo=True)
Base.metadata.create_all(e)

# Creating a region called 'default'. This is where stuff is cached.
# dogpile.cache.memory is just one way to store cache.

regions = {}
regions['default'] = make_region(key_mangler=md5_key_mangler)\
    .configure('dogpile.cache.memory')

Session = sessionmaker(bind=e, query_cls=query_callable(regions))
sess = Session()

# Creating configs pointing to persons.

sess.add(Config(person_ref=Person(name='Arthur Dent')))
sess.add(Config(person_ref=Person(name='Ford Prefect')))
sess.commit()

# joinedload deactivates lazy loading for person_ref.

conf = sess.query(Config).options(joinedload(Config.person_ref), FromCache("default")).first()
sess.commit()
sess.close()


print("_____NO MORE SQL!___________")


conf = sess.query(Config).options(joinedload(Config.person_ref), FromCache("default")).first()
print(conf.person_ref.name)
