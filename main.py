import ccxt
import asyncio
from config import TOKEM_API
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart,Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile,BotCommand

import re
import requests
a = True
bot = Bot(token=TOKEM_API)
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
    photo = FSInputFile('start.png')
    await message.answer_photo(
        photo = photo,
        caption=f'<b>Hi {message.from_user.first_name}, Im a bot that can convert cryptocurrency</b>\nto get started, check out /help', parse_mode='HTML')
@dp.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('To use the bot you just need to enter the cryptocurrency you want to know the price of\n'
                         'You can find out the cost of all cryptocurrencies that are on the <a href="https://www.binance.com">Binance</a> exchange\n'
                         '\n'
                         "Example: 10 sol to usdt\n",
                         parse_mode="HTML",disable_web_page_preview=True
                         )




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
                response = requests.post(url, json=payload).json()
                usdt_to_kzt = float(response['data'][0]['adv']['price'])


                ticker = exchange.fetch_ticker(f"{from_symbol}/USDT")
                crypto_price_usdt = float(ticker['last'])


                total_in_kzt = amount * crypto_price_usdt * usdt_to_kzt

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"📊 {from_symbol} Chart",
                                          url=f"https://www.binance.com/ru-KZ/trade/{from_symbol}_USDT?type=spot")],
                    [InlineKeyboardButton(text="❌ Delete", callback_data="delete_msg")]
                ])

                await message.answer(
                    f"✅<b>{amount} {from_symbol} {to_symbol}</b>\n\n"
                    f"<b>Result:</b> {total_in_kzt:,.2f} KZT\n",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:

                ticker = exchange.fetch_ticker(f"{from_symbol}/{to_symbol}")
                price = float(ticker['last'])
                result = amount * price

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=f"📊 {from_symbol} Chart",
                                          url=f"https://www.binance.com/ru-KZ/trade/{from_symbol}_{to_symbol}?type=spot")],
                    [InlineKeyboardButton(text="❌ Delete", callback_data="delete_msg")]
                ])

                await message.answer(
                    f"✅<b>{amount} {from_symbol} to {to_symbol}</b>\n\n"
                    f"Result: {result:,.2f} USDT\n"
                    ,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )

        except Exception:
            await message.answer(
                "<b>❌ Wronng! Check format and currency.</b>\n"
                "<pre>Example: 10 sol to usdt</pre>",
                parse_mode="HTML"
            )


    elif text.isalpha() and len(text) <= 10:
        try:
            symbol = text.upper()
            ticker = exchange.fetch_ticker(f"{symbol}/USDT")
            price = float(ticker['last'])
            percent = ticker.get('percentage', 0)


            change_icon = " 🟩" if percent > 0 else "🟥"
            sign = "+" if percent > 0 else ""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"📊 {symbol} Chart",
                                      url=f"https://www.binance.com/ru-KZ/trade/{symbol}_USDT?type=spot")]
            ])

            await message.answer(
                f"<b>{symbol} price:</b>\n"
                f"💵 {price:,.2f} USDT"
                f' |  {change_icon} {sign} {percent}% (24h)',
                parse_mode="HTML",
                reply_markup=keyboard
            )
        except:
            pass


@dp.callback_query(F.data == "delete_msg")
async def delete_message(callback: CallbackQuery):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await callback.answer('Message deleted', show_alert=False)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    print('go')
    asyncio.run(main())
