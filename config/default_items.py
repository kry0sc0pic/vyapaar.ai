from pydantic import BaseModel

class Item(BaseModel):
    name: str
    quantity: int


fallback_products = [
    Item(
        name="Harvest Gold Bread",
        quantity=30
    )
]