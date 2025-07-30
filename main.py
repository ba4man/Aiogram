import ccxt.async_support as ccxt
import asyncio
import aiohttp
from config import TOKEM_API
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile, BotCommand
import re
import os

bot = Bot(token=os.getenv("BOT_TOKEN", TOKEM_API))
dp = Dispatcher()

exchange = ccxt.binance()
convert_pattern = re.compile(r"^\d+(\.\d+)?\s+[a-zA-Z]+\s+to\s+[a-zA-Z]+$")

async def set_commands():
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="How to use the bot"),
    ]
    await bot.set_my_commands(commands)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    photo_path = 'start.png'
    if os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        await message.answer_photo(photo=photo,
                                   caption=f'<b>Hi {message.from_user.first_name}, I can convert cryptocurrency</b>\nUse /help',
                                   parse_mode='HTML')
    else:
        await message.answer(f'Hi {message.from_user.first_name}, I can convert cryptocurrency.\nUse /help')

@dp.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('To use the bot enter:\n'
                         'Example: 10 sol to usdt\n'
                         'Or just type: BTC\n',
                         parse_mode="HTML")

@dp.message()
async def convert_currency(message: Message):
    text = message.text.strip().lower()

    if convert_pattern.match(text):
        parts = text.split()
        amount = float(parts[0])
        from_symbol = parts[1].upper()
        to_symbol = parts[3].upper()

        try:
            if to_symbol == "KZT":
                url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
                payload = {
                    "page": 1,
                    "rows": 1,
                    "payTypes": [],
                    "asset": "USDT",
                    "fiat": "KZT",
                    "tradeType": "SELL"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload) as resp:
                        response = await resp.json()

                usdt_to_kzt = float(response['data'][0]['adv']['price'])

                ticker = await exchange.fetch_ticker(f"{from_symbol}/USDT")
                crypto_price_usdt = float(ticker['last'])

                total_in_kzt = amount * crypto_price_usdt * usdt_to_kzt

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"📊 {from_symbol} Chart",
                                          url=f"https://www.binance.com/ru-KZ/trade/{from_symbol}_USDT?type=spot")],
                    [InlineKeyboardButton(text="❌ Delete", callback_data="delete_msg")]
                ])

                await message.answer(
                    f"✅<b>{amount} {from_symbol} → {to_symbol}</b>\n\n"
                    f"<b>Result:</b> {total_in_kzt:,.2f} KZT\n",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                ticker = await exchange.fetch_ticker(f"{from_symbol}/{to_symbol}")
                price = float(ticker['last'])
                result = amount * price

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"📊 {from_symbol} Chart",
                                          url=f"https://www.binance.com/ru-KZ/trade/{from_symbol}_{to_symbol}?type=spot")],
                    [InlineKeyboardButton(text="❌ Delete", callback_data="delete_msg")]
                ])

                await message.answer(
                    f"✅<b>{amount} {from_symbol} → {to_symbol}</b>\n\n"
                    f"Result: {result:,.2f} {to_symbol}\n",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        except Exception as e:
            await message.answer(
                f"<b>❌ Error: {e}</b>\n"
                "<pre>Example: 10 sol to usdt</pre>",
                parse_mode="HTML"
            )

    elif text.isalpha() and len(text) <= 10:
        try:
            symbol = text.upper()
            ticker = await exchange.fetch_ticker(f"{symbol}/USDT")
            price = float(ticker['last'])
            percent = ticker.get('percentage', 0)

            change_icon = "🟩" if percent > 0 else "🟥"
            sign = "+" if percent > 0 else ""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"📊 {symbol} Chart",
                                      url=f"https://www.binance.com/ru-KZ/trade/{symbol}_USDT?type=spot")]
            ])

            await message.answer(
                f"<b>{symbol} price:</b>\n"
                f"💵 {price:,.2f} USDT | {change_icon} {sign}{percent}% (24h)",
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except:
            await message.answer("<b>❌ Unknown symbol.</b>", parse_mode="HTML")


@dp.callback_query(F.data == "delete_msg")
async def delete_message(callback: CallbackQuery):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.answer('Message deleted', show_alert=False)

async def main():
    await set_commands()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
