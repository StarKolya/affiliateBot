from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="admin")


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    """Admin panel entry point. Verifies role before exposing actions."""
    ...


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
