from typing import Optional
from pydantic import BaseModel, validator, Field
from typing_extensions import Annotated


#  Чтобы в полной мере использовать FastAPI,
#  модели Пони должны работать со схемами pydantic


class ProducerOutForProducts(BaseModel):
    id: int
    name: str
    country: str


class ProductsOut(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    description: Optional[str]
    producer: ProducerOutForProducts

    @validator('producer', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, value):  # Добавляет всю инфу о продуктах
        if hasattr(value, "to_dict"):
            value = value.to_dict()
        return value

    class Config:
        orm_mode = True


class ProductOutForProducer(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    description: Optional[str] = Field(None, title="The description of the products", max_length=20000)

    class Config:
        orm_mode = True


class ProducerOut(BaseModel):
    id: int
    name: str
    country: str
    products: list[ProductOutForProducer]

    @validator('products', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        new_values = list()  # Добавляет всю инфу о продуктах
        for v in values:
            if hasattr(v, "to_dict"):
                new_values.append(v.to_dict())
        return new_values

    class Config:
        orm_mode = True


class NewProducts(BaseModel):
    id: Annotated[int, Field(title="1", ge=1, le=10000)] = 1
    name: Annotated[str, Field(title="The description of the products", max_length=20000)] = 'name'
    price: Annotated[int, Field(title="1", ge=0, le=10000)] = 100
    quantity: Annotated[int, Field(title="1", ge=0, le=10000)] = 100
    description: Annotated[Optional[str], Field(max_length=20000)] = 'description'
    producer: Annotated[int, Field(title="1", ge=1, le=10000)] = 1


class EditProducts(BaseModel):
    name: Annotated[str, Field(title="The description of the products", max_length=20000)] = 'name'
    price: Annotated[int, Field(title="1", ge=0, le=10000)] = 100
    quantity: Annotated[int, Field(title="1", ge=0, le=10000)] = 100
    description: Annotated[Optional[str], Field(max_length=20000)] = 'description'
    producer: Annotated[int, Field(title="1", ge=1, le=10000)] = 1


class CoolLvL(BaseModel):
    id: Annotated[int, Field(title="1", ge=1, le=10000)] = 1
    name: Annotated[str, Field(max_length=20)] = 'name'
    country: Annotated[str, Field(max_length=20)] = 'Russia'
    quantity: Annotated[int, Field(title="1", ge=0, le=10000)] = 100

    class Config:
        orm_mode = True


class NewProducer(BaseModel):
    id: Annotated[int, Field(title="1", ge=1, le=10000)] = 1
    name: Annotated[str, Field(max_length=20)] = 'name'
    country: Annotated[str, Field(max_length=20)] = 'Russia'

    class Config:
        orm_mode = True


class EditProducer(BaseModel):
    name: Annotated[str, Field(max_length=20)] = 'name'
    country: Annotated[str, Field(max_length=20)] = 'Russia'


class SortedProductsForProducer(BaseModel):
    products: list[ProductOutForProducer]

    @validator('products', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        new_values = list()  # Добавляет всю инфу о продуктах
        for v in values:
            if hasattr(v, "to_dict"):
                new_values.append(v.to_dict())
        return new_values

    class Config:
        orm_mode = True


class UserEnter(BaseModel):
    name: Annotated[str, Field(max_length=20)] = 'name'
    password: Annotated[str, Field(max_length=20)] = 'qwerty123'


class AdminEnter(BaseModel):
    name: Annotated[str, Field(max_length=20)] = 'name'
    password: Annotated[str, Field(max_length=20)] = 'qwerty123'


class UserOut(BaseModel):
    name: Annotated[str, Field(max_length=20)] = 'name'
    admin_rights: bool = False
    disabled: Optional[bool] = None

    class Config:
        orm_mode = True


class UserInDB(UserOut):
    hashed_password: str

