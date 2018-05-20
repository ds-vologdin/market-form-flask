from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

from settings import DATABASES

from flask import json


Base = declarative_base()


class MainCategoryProduct(Base):
    __tablename__ = 'main_category_product'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)

    categorys_product = relationship(
        'CategoryProduct', back_populates='main_category_product'
    )

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<main_category_product({0})>'.format(self.name)


class CategoryProduct(Base):
    __tablename__ = 'category_product'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    main_category_product_id = Column(
        Integer, ForeignKey('main_category_product.id')
    )

    main_category_product = relationship(
        'MainCategoryProduct', back_populates='categorys_product'
    )
    products = relationship('Product', back_populates='category_product')

    def __init__(self, name, main_category_product_id):
        self.name = name
        self.main_category_product_id = main_category_product_id

    def __repr__(self):
        return '<category_product({0}, {1})>'.format(
            self.name, self.main_category_product_id
        )


class ImagesProduct(Base):
    __tablename__ = 'images_product'
    id = Column(Integer, primary_key=True)
    id_product = Column(Integer, ForeignKey('product.id'))
    file = Column(String(200))
    priority = Column(Integer)

    product = relationship('Product', back_populates='images')

    def __init__(self, id_product, file, priority=10):
        self.id_product = id_product
        self.file = file
        self.priority = priority
        pass


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    cost = Column(Float)
    category_product_id = Column(Integer, ForeignKey('category_product.id'))
    parameters = Column(JSONB)
    # тип parameters (JSONB) - привязывает нас к postgresql
    # пока не понял как обратиться через sqlalchemy к вложенному элементу json
    # однако на крайняк можно пользовать raw-sql:
    # r = engine.execute(
    #     "SELECT * FROM product
    #     WHERE product.parameters->'Память и процессор'->'parameters'->'Количество ядер процессора' @> '8';"
    # )
    # Хотя может лучше иметь плоский словарь?..

    images = relationship('ImagesProduct', back_populates='product')
    category_product = relationship(
        'CategoryProduct', back_populates='products'
    )

    def __init__(self, name, cost, category_product_id, parameters):
        self.name = name
        self.cost = cost
        self.category_product_id = category_product_id
        self.parameters = parameters

    def __repr__(self):
        return '<product({0}, {1}, {2}, {3})>'.format(
            self.name, self.cost, self.category_product_id, self.parameters
        )

    def convert_to_dict(self):
        return {
            'name': self.name,
            'cost': self.cost,
            'parameters': self.sorted_parameters(),
        }

    def sorted_parameters(self):
        product_sorted_parameters = sorted(
            self.parameters.items(),
            key=lambda x: x[1].get('priority')
        )
        product_sorted_parameters = (
            (
                category_parameters[0],
                (
                    category_parameters[1].get('main_parameters'),
                    category_parameters[1].get('parameters')
                )
            )
            for category_parameters in product_sorted_parameters
        )
        return product_sorted_parameters

    def flat_parameters(self):

        pass


default_db = DATABASES['default']
engine = create_engine(
    '{0}://{1}:{2}@{3}:{4}/{5}'.format(
        default_db['ENGINE'], default_db['USER'], default_db['PASSWORD'],
        default_db['HOST'], default_db['PORT'], default_db['DB']
    ),
    json_serializer=json.dumps,
    echo=True,
)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
session = Session()
