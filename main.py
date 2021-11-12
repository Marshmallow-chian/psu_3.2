import os.path
import uvicorn
from pony.orm import db_session, commit
from models import db, Producer, User, Products
from security.s_main import (get_password_hash, get_current_active_user, get_current_active_admin,
                             ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, create_access_token, get_current_active)
from scheme import (ProductsOut, ProducerOut, NewProducts, EditProducts, NewProducer, EditProducer, CoolLvL,
                    UserOut, UserEnter, AdminEnter)
from security.s_scheme import Token
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, Body, Security, Depends, status, HTTPException
import os
from config import secret_key, administrator

# использовать exception
# TODO: add hashed_password -> password

app = FastAPI()
my_db = 'Manufacturer_and_Products.sqlite'

SECRET_KEY = None


@app.on_event("startup")
async def start_app():
    global SECRET_KEY
    """Выполняется при старте приложения"""
    # Прежде чем мы сможем сопоставить сущности с базой данных,
    # нам нужно подключиться, чтобы установить соединение с ней.
    # Это можно сделать с помощью метода bind()
    create_db = True
    if os.path.isfile(my_db):
        create_db = False
    SECRET_KEY = secret_key()
    db.bind(provider='sqlite', filename=my_db, create_db=create_db)
    db.generate_mapping(create_tables=create_db)
    ADMINISTRATOR = administrator()
    with db_session:
        if not User.exists(name=ADMINISTRATOR['name']):
            User(**ADMINISTRATOR)
            commit()


# ----------------------------------------------------------------------------------------------------

@app.get('/api/administrator', tags=['administrator'])
async def get_all_administrator():
    with db_session:
        administrators = User.select(admin_rights=True)
        # преобразуем запрос в SQL, а затем отправим в базу данных
        all_administrators = []
        for i in administrators:
            all_administrators.append(UserOut.from_orm(i))
    return all_administrators


@app.post('/api/administrator/new', tags=['administrator'])
async def new_admin(admin: AdminEnter = Body(...), current_user: User = Security(get_current_active_admin,
                                                                                 scopes=["admin"])):
    with db_session:
        n_admin = admin.dict()
        if User.exists(name=admin.name):
            return 'администратор с таким именем уже существует'

        n_admin['hashed_password'] = n_admin.pop('password')
        password = n_admin['hashed_password']
        n_admin['hashed_password'] = get_password_hash(password)

        User(**n_admin)
        commit()
        return UserOut.from_orm(admin)


# ----------------------------------------------------------------------------------------------------


@app.post('/api/user/new', tags=['user'])
async def new_user(user: UserEnter = Body(...)):  # любой
    with db_session:
        n_user = user.dict()
        print(User.exists(name=user.name))
        print(user)
        if User.exists(name=user.name):
            return 'пользователь с таким именем уже существует'

        n_user['hashed_password'] = n_user.pop('password')
        password = n_user['hashed_password']
        n_user['hashed_password'] = get_password_hash(password)

        User(**n_user)
        commit()
        return UserOut.from_orm(user)


@app.get('/api/user', tags=['user'])
async def get_all_users():  # любой
    with db_session:
        users = User.select(admin_rights=False)  # преобразуем запрос в SQL, а затем отправим в базу данных
        all_users = []
        for i in users:
            all_users.append(UserOut.from_orm(i))
    return all_users


@app.get("/users/me/", response_model=UserOut, tags=['user'])
async def read_users_me(current_user: User = Depends(get_current_active)):
    return current_user


@app.get("/users/me/items/", tags=['user'])
async def read_own_items(current_user: User = Depends(get_current_active)):
    return [{"owner": current_user.name}]


# -----------------------------------------------------------------------------------------


@app.post("/token", response_model=Token, tags=['token'])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    with db_session:
        user = authenticate_user(form_data.username, form_data.password, form_data.scopes)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)  # 30 min
        access_token = create_access_token(data={"sub": user.name, "scopes": form_data.scopes},
                                           expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}


# -----------------------------------------------------------------------------------------


@app.get('/api/products', tags=['products'])
async def get_all_products():  # любой
    with db_session:
        products = Products.select()  # преобразуем запрос в SQL, а затем отправим в базу данных
        all_products = []
        for i in products:
            all_products.append(ProductsOut.from_orm(i))
    return all_products


@app.get('/api/product/get_average_products', tags=['products'])
async def get_average(minimum: int, maximum: int):  # любой
    with db_session:
        products = Products.select(lambda p: (minimum <= p.price) and (p.price <= maximum))[::]  # работает
        all_products = []
        for i in products:
            all_products.append(ProductsOut.from_orm(i))
        return all_products


@app.get('/api/product/{product_id}', tags=['products'])
async def get_product(product_id: int):  # любой
    with db_session:
        if product_id > 1999999999 or product_id < 0:
            return 'ошибка id'
        if Products.exists(id=product_id):
            product = Products.get(id=product_id)
            return ProductsOut.from_orm(product)
        else:
            return 'товара с таким id не существует'


@app.put('/api/product/buy/{product_id}', tags=['products.buy'])
async def product_buy(product_id: int, count: int, current_user: User = Security(get_current_active_user, scopes=["user"])):
    with db_session:
        if product_id > 1999999999 or product_id < 0:
            return 'ошибка id'
        if Products.exists(id=product_id):
            product = Products.get(id=product_id)
            if count <= 0:
                return 'error: попытка купить отрицательное число товаров'
            product.quantity = product.quantity - count
            if product.quantity < 0:
                return 'такого количесвта товаров нет на складе'
            print(product.quantity)
            commit()
            return ProductsOut.from_orm(Products[product_id])
        return 'товара с таким id не существует'


@app.post('/api/product/new', tags=['products'])
async def new_product(n_product: NewProducts = Body(...), current_user: User = Security(get_current_active_admin,
                                                                                        scopes=["admin"])):
    with db_session:

        if n_product.id > 1999999999 or n_product.id < 0:
            return 'ошибка id'
        product = n_product.dict()

        if Products.exists(id=int(n_product.id)):
            return 'товар с таким id уже существует'

        if not Producer.exists(id=int(n_product.producer)):
            return 'Производителя с таким id не существует'

        Products(**product)
        commit()
        return n_product


@app.put('/api/product/edit/{product_id}', tags=['products'])
async def edit_product(product_id: int, edit_pr: EditProducts = Body(...)):
                      # current_user: User = Security(get_current_active_admin, scopes=["admin"])):
    with db_session:

        if product_id > 1999999999 or product_id < 0:
            return 'ошибка id'

        if Products.exists(id=product_id):
            product = edit_pr.dict(exclude_unset=True, exclude_none=True)
            if 'producer' in product and not Producer.exists(id=product['producer']):
                return 'Производителя с таким id не существует'
            Products[product_id].set(**product)
            commit()
            return ProductsOut.from_orm(Products[product_id])
        return 'товара с таким id не существует'


@app.delete('/api/product/delete/{product_id}', tags=['products'])
async def delete_product(product_id: int, current_user: User = Security(get_current_active_admin, scopes=["admin"])):
    with db_session:
        if product_id > 1999999999 or product_id < 0:
            return 'ошибка id'
        if Products.exists(id=product_id):
            Products[product_id].delete()
            commit()
            return "Объект удалён"
        return "производителя с таким id не существует"


# ----------------------------------------------------------------------------------------


@app.get('/api/producer/get_cool_producers', tags=['producers'])
async def get_cool(cool_level: int):
    with db_session:
        producer = Producer.select(lambda p: len(p.products) >= cool_level)[::]  # работает
        all_producer = []
        for i in producer:
            quantity = len(i.products)
            i = i.to_dict() | {'quantity': quantity}
            print(i)
            print(CoolLvL(**i))
            all_producer.append(CoolLvL(**i))
        return all_producer


@app.get('/api/producers', tags=['producers'])
async def get_all_producers():
    with db_session:
        producer = Producer.select()[:]  # преобразуем запрос в SQL, а затем отправим в базу данных
        all_producer = []
        for i in producer:
            all_producer.append(ProducerOut.from_orm(i))
    return all_producer


@app.get('/api/producer/{producer_id}', tags=['producers'])
async def get_producer(producer_id: int):  # любой
    with db_session:
        if producer_id > 1999999999 or producer_id < 0:
            return 'ошибка id'
        if Producer.exists(id=producer_id):
            producer = Producer.get(id=producer_id)
            return ProducerOut.from_orm(producer)
        else:
            return 'товара с таким id не существует'


@app.post('/api/producer/new', tags=['producers'])
async def new_producer(n_producer: NewProducer = Body(...)):  # любой
    with db_session:
        producer = n_producer.dict()
        if producer['id'] > 1999999999 or producer['id'] < 0:
            return 'ошибка id'
        if Producer.exists(id=int(n_producer.id)):
            return 'производитель с таким id уже существует'

        producer = Producer(**producer)
        commit()
        return ProducerOut.from_orm(producer)


@app.put('/api/producer/edit/{producer_id}', tags=['producers'])
async def edit_producer(producer_id: int, edit_pr: EditProducer = Body(...),
                        current_user: User = Security(get_current_active_admin, scopes=["admin"])):
    with db_session:
        if producer_id > 1999999999 or producer_id < 0:
            return 'ошибка id'
        if Producer.exists(id=producer_id):
            producer = edit_pr.dict(exclude_unset=True, exclude_none=True)
            Producer[producer_id].set(**producer)
            commit()
            return ProducerOut.from_orm(Producer[producer_id])
        return 'производителя с таким id не существует'


@app.delete('/api/producer/delete/{producer_id}', tags=['producers'])
async def delete_producer(producer_id: int, current_user: User = Security(get_current_active_admin, scopes=["admin"])):
    with db_session:
        if producer_id > 1999999999 or producer_id < 0:
            return 'ошибка id'
        if Producer.exists(id=producer_id):
            Producer[producer_id].delete()
            commit()
            return "Объект удалён"
        return "производителя с таким id не существует"


@app.get('/api/producer/{producer_id}/products', tags=['producers'])
async def sorted_products(producer_id: int):  # любой
    with db_session:
        if producer_id > 1999999999 or producer_id < 0:
            return 'ошибка id'
        if Producer.exists(id=producer_id):
            producer = Producer.get(id=producer_id)
            pr = producer.products.select().order_by(Products.price)[::]
            return ProducerOut(**(producer.to_dict() | {'products': pr}))
        return 'Производителя с таким id не существует'


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
