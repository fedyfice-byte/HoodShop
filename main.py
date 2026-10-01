import os
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from sqlalchemy import String, Integer, Float, DateTime, Text, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv(
    "WEBAPP_URL",
    "https://humanity-christine-place-scripts.trycloudflare.com"
)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "hoodshop-admin")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./hoodshop.db"
)

BASE = Path(__file__).resolve().parent
WEB_DIR = BASE / "web"
STATIC_DIR = WEB_DIR / "static"
INDEX_FILE = WEB_DIR / "index.html"

STATIC_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# DATABASE
# =========================

class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float] = mapped_column(Float, default=0)
    category: Mapped[str] = mapped_column(
        String(100),
        default="Boshqa"
    )
    image: Mapped[str] = mapped_column(
        String(1000),
        default=""
    )
    stock: Mapped[int] = mapped_column(
        Integer,
        default=10
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    telegram_id: Mapped[str] = mapped_column(
        String(100),
        default=""
    )
    username: Mapped[str] = mapped_column(
        String(255),
        default=""
    )
    customer_name: Mapped[str] = mapped_column(
        String(255),
        default=""
    )
    phone: Mapped[str] = mapped_column(
        String(100),
        default=""
    )
    address: Mapped[str] = mapped_column(
        Text,
        default=""
    )
    items: Mapped[str] = mapped_column(
        Text,
        default="[]"
    )
    total: Mapped[float] = mapped_column(
        Float,
        default=0
    )
    status: Mapped[str] = mapped_column(
        String(100),
        default="new"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


engine = create_async_engine(
    DATABASE_URL,
    echo=False
)

SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


# =========================
# HELPERS
# =========================

def product_dict(p: Product):
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description or "",
        "price": p.price,
        "category": p.category or "Boshqa",
        "image": p.image or "",
        "stock": p.stock,
    }


def order_dict(o: Order):
    try:
        items = json.loads(o.items or "[]")
    except Exception:
        items = []

    return {
        "id": o.id,
        "telegram_id": o.telegram_id,
        "username": o.username,
        "customer_name": o.customer_name,
        "phone": o.phone,
        "address": o.address,
        "items": items,
        "total": o.total,
        "status": o.status,
        "created_at": o.created_at.isoformat()
        if o.created_at else "",
    }


def check_admin(password):
    if password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=403,
            detail="Admin parol noto'g'ri"
        )


# =========================
# APP
# =========================

app = FastAPI(
    title="HoodShop",
    version="2.0.0"
)

# ENG MUHIM QISM:
# Telegramdan yuklangan rasmlar shu orqali ishlaydi.
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static"
)


# =========================
# DATABASE INIT
# =========================

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all
        )

    # Eski DB saqlanadi.
    # Faqat bo'sh DB bo'lsa demo mahsulot yaratamiz.
    async with SessionLocal() as session:
        result = await session.execute(
            select(Product).limit(1)
        )

        if result.scalar_one_or_none() is None:
            demo = [
                Product(
                    name="Hoodie Black",
                    description="Material: Paxta\nO‘lchamlar: S–XL",
                    price=299000,
                    category="Hoodies",
                    image="",
                    stock=10
                ),
                Product(
                    name="Oversize T-Shirt",
                    description="Material: Paxta\nO‘lchamlar: S–XL",
                    price=149000,
                    category="Futbolkalar",
                    image="",
                    stock=10
                )
            ]

            session.add_all(demo)
            await session.commit()


# =========================
# WEB
# =========================

@app.get("/", response_class=HTMLResponse)
async def home():
    if not INDEX_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail="web/index.html topilmadi"
        )

    return INDEX_FILE.read_text(
        encoding="utf-8"
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "shop": "HoodShop"
    }


# =========================
# PRODUCTS API
# =========================

@app.get("/api/products")
async def products(
    category: Optional[str] = None
):
    async with SessionLocal() as session:

        query = select(Product).order_by(
            Product.id.desc()
        )

        if category and category != "Barchasi":
            query = query.where(
                Product.category == category
            )

        result = await session.execute(query)

        return [
            product_dict(p)
            for p in result.scalars().all()
        ]


@app.get("/api/products/{product_id}")
async def product(product_id: int):

    async with SessionLocal() as session:

        result = await session.execute(
            select(Product).where(
                Product.id == product_id
            )
        )

        p = result.scalar_one_or_none()

        if not p:
            raise HTTPException(
                status_code=404,
                detail="Mahsulot topilmadi"
            )

        return product_dict(p)


# =========================
# ORDERS
# =========================

@app.post("/api/orders")
async def create_order(request: Request):

    data = await request.json()

    items = data.get("items", [])

    if not items:
        raise HTTPException(
            status_code=400,
            detail="Savat bo'sh"
        )

    async with SessionLocal() as session:

        # Narxlarni DBdan qayta hisoblaymiz.
        clean_items = []
        total = 0

        for item in items:

            product_id = int(
                item.get("id", 0)
            )

            quantity = max(
                1,
                int(item.get("quantity", 1))
            )

            result = await session.execute(
                select(Product).where(
                    Product.id == product_id
                )
            )

            p = result.scalar_one_or_none()

            if not p:
                continue

            if p.stock <= 0:
                continue

            quantity = min(
                quantity,
                p.stock
            )

            subtotal = p.price * quantity
            total += subtotal

            clean_items.append({
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "quantity": quantity,
                "subtotal": subtotal,
            })

        if not clean_items:
            raise HTTPException(
                status_code=400,
                detail="Mahsulotlar topilmadi"
            )

        order = Order(
            telegram_id=str(
                data.get("telegram_id", "")
            ),
            username=str(
                data.get("username", "")
            ),
            customer_name=str(
                data.get("customer_name", "")
            ),
            phone=str(
                data.get("phone", "")
            ),
            address=str(
                data.get("address", "")
            ),
            items=json.dumps(
                clean_items,
                ensure_ascii=False
            ),
            total=total,
            status="new"
        )

        session.add(order)

        # Stockni kamaytiramiz.
        for item in clean_items:

            result = await session.execute(
                select(Product).where(
                    Product.id == item["id"]
                )
            )

            p = result.scalar_one_or_none()

            if p:
                p.stock = max(
                    0,
                    p.stock - item["quantity"]
                )

        await session.commit()
        await session.refresh(order)

        return {
            "success": True,
            "order": order_dict(order)
        }


# =========================
# ADMIN
# =========================

@app.get("/api/admin/orders")
async def admin_orders(password: str):

    check_admin(password)

    async with SessionLocal() as session:

        result = await session.execute(
            select(Order).order_by(
                Order.id.desc()
            )
        )

        return [
            order_dict(o)
            for o in result.scalars().all()
        ]


@app.get("/api/admin/products")
async def admin_products(password: str):

    check_admin(password)

    async with SessionLocal() as session:

        result = await session.execute(
            select(Product).order_by(
                Product.id.desc()
            )
        )

        return [
            product_dict(p)
            for p in result.scalars().all()
        ]


@app.post("/api/admin/products")
async def admin_create_product(
    request: Request
):

    data = await request.json()

    check_admin(
        data.get("password")
    )

    async with SessionLocal() as session:

        p = Product(
            name=str(
                data.get("name", "")
            ).strip(),
            description=str(
                data.get("description", "")
            ),
            price=float(
                data.get("price", 0)
            ),
            category=str(
                data.get(
                    "category",
                    "Boshqa"
                )
            ),
            image=str(
                data.get("image", "")
            ),
            stock=int(
                data.get("stock", 10)
            )
        )

        if not p.name:
            raise HTTPException(
                status_code=400,
                detail="Nom kerak"
            )

        session.add(p)

        await session.commit()
        await session.refresh(p)

        return product_dict(p)


@app.delete(
    "/api/admin/products/{product_id}"
)
async def admin_delete_product(
    product_id: int,
    password: str
):

    check_admin(password)

    async with SessionLocal() as session:

        result = await session.execute(
            select(Product).where(
                Product.id == product_id
            )
        )

        p = result.scalar_one_or_none()

        if not p:
            raise HTTPException(
                status_code=404,
                detail="Topilmadi"
            )

        await session.delete(p)
        await session.commit()

        return {
            "success": True
        }


# =========================
# TELEGRAM BOT
# =========================

asyncio.set_event_loop(
    asyncio.new_event_loop()
)

dp = Dispatcher()

bot = Bot(
    token=BOT_TOKEN
)


@dp.message(CommandStart())
async def start_command(
    message: types.Message
):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍 SHOP",
                    web_app=WebAppInfo(
                        url=WEBAPP_URL
                    )
                )
            ]
        ]
    )

    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "HoodShop'ga xush kelibsiz.\n\n"
        "Katalogni ko‘rish va buyurtma berish "
        "uchun SHOP tugmasini bosing.",
        reply_markup=keyboard
    )


async def start_bot():

    print("HoodShopBot ishga tushdi.")

    await dp.start_polling(bot)


@app.on_event("startup")
async def startup():

    await init_db()

    asyncio.create_task(
        start_bot()
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
