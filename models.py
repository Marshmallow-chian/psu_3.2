from pony.orm import *

db = Database()


class Producer(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=False)
    country = Required(str)
    products = Set('Products')


class Products(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str, unique=False)
    price = Required(float)
    quantity = Required(int)
    description = Optional(str)
    producer = Required(Producer)
    # кол-во продуктов


class User(db.Entity):
    name = PrimaryKey(str)
    hashed_password = Required(str, unique=False)
    admin_rights = Required(bool, default=False)
    disabled: Required(bool, unique=False)


    '''_roles = Required(Json, default=dict(user=''))

    @property
    def roles(self):
        return list(self._roles)

    @roles.setter
    def roles(self, value: list[str]):
        self._roles = {i: '' for i in value}

# enum в fast-api при создании

user = User[0]
print(user.roles)
user.roles = ['user', 'admin']
'''

#  наследование от пони user.exist username.admin