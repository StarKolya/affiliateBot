from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.filters import IsAdmin
from bot.keyboards.admin_kb import admin_menu_kb

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer("Welcome to the admin panel.", reply_markup=admin_menu_kb())


# --- Job management ---

async def handle_create_job(message: Message) -> None:
    ...


async def handle_delete_job(message: Message) -> None:
    ...


async def handle_assign_question(message: Message) -> None:
    ...


# --- Application management ---

async def handle_list_applications(message: Message) -> None:
    ...


async def handle_update_application_status(message: Message) -> None:
    ...


# --- Payout management ---

async def handle_list_payouts(message: Message) -> None:
    ...


async def handle_approve_payout(message: Message) -> None:
    ...


async def handle_reject_payout(message: Message) -> None:
    ...
