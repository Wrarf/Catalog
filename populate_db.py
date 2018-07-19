from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Add categories to the db
baseball = Category(name="Baseball")
session.add(baseball)
session.commit()

basketball = Category(name="Basketball")
session.add(baseball)
session.commit()

bodybuilding = Category(name="Bodybuilding")
session.add(bodybuilding)
session.commit()

jogging = Category(name="Jogging")
session.add(jogging)
session.commit()

tennis = Category(name="Tennis")
session.add(tennis)
session.commit()

# Add a fake user for tests on CRUD
test_user = User(username="Tester", email="fakemail@doesntexist.com")
session.add(test_user)
session.commit()

# Add items
shoes = Item(
    category=basketball,
    name="Shoes",
    description="A pair of red shoes.",
    creator=test_user)
session.add(shoes)
session.commit()

basket_ball = Item(
    category=basketball,
    name="Basket Ball",
    description="A basket ball.",
    creator=test_user)
session.add(basket_ball)
session.commit()

baseball_glove = Item(
    category=baseball,
    name="Baseball Glove",
    description="A good glove.",
    creator=test_user)
session.add(baseball_glove)
session.commit()

dumbbell = Item(
    category=bodybuilding,
    name="Dumbbell",
    description="4kg dumbbell.",
    creator=test_user)
session.add(dumbbell)
session.commit()

racket = Item(
    category=tennis,
    name="Tennis Racket",
    description="A yellow tennis racket.",
    creator=test_user)
session.add(racket)
session.commit()
