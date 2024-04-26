import aiohttp
import os
import re
from aiohttp import ContentTypeError
from common.db.model import create_tg_user_search_query, get_latest_search_query, upsert_user_returning_id
from common.domain.schema import SearchPatentResponse
from pydantic import BaseModel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from telegram_bot.infrastructure.db import with_db_connection
from typing import List, Optional

RASPATENT_SCRAPER_URL = os.getenv("RASPATENT_SCRAPER_URL")
GIGA_CHAT_API_URL = os.getenv("GIGA_CHAT_API_URL")

SEARCH_TEXT, PAGE_NAVIGATION, SIMILAR_PAGE_NAVIGATION = range(3)

SEARCH_QUERY = range(1)


async def upsert_user(connection, effective_user):
    return await upsert_user_returning_id(connection, id=effective_user.id, username=effective_user.username, first_name=effective_user.first_name, last_name=effective_user.last_name, language_code=effective_user.language_code, is_premium=effective_user.is_premium)


def escape_text(text: Optional[str]) -> Optional[str]:
    if text:
        return re.escape(text).replace("=", "\\=").replace("_", "\\_").replace("!", "\\!").replace('>', '\\>').replace('<', '\\<')
    return text


async def search(text, update: Update, context: CallbackContext, limit=10, offset=0, from_callback_query=False):
    reply_to = update.callback_query.message if from_callback_query else update.message

    await reply_to.reply_text(f"search query: {text}, page: {offset // limit + 1}")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{RASPATENT_SCRAPER_URL}/rospatent_scraper/search_full_info_extended/?patent_description={text}&limit={limit}&offset={offset}"
        ) as response:
            result_json = await response.json()
            search_patent_response = SearchPatentResponse.validate(result_json)
            await reply_to.reply_text(f"Total patents: {search_patent_response.total}")
            for patent in search_patent_response.patents:
                patent_url = f'https://searchplatform.rospatent.gov.ru/doc/{patent.id}'
                content_types = {'snippet': 'snippet_ru', 'abstract': 'abstract_ru', 'claims': 'claims_ru', 'description': 'description_ru'}
                selected_content_type = None
                button_rows = []

                for ct_key, ct_value in content_types.items():
                    if getattr(patent, ct_value):
                        if selected_content_type is None:
                            selected_content_type = ct_key
                            description = getattr(patent, ct_value)
                            break

                content_type_code = ''.join([ct_key[0] for ct_key, ct_value in content_types.items() if getattr(patent, ct_value)])
                for ct_key, ct_value in content_types.items():
                    if getattr(patent, ct_value):
                        original_button_text = f"{'🔵 ' if ct_key == selected_content_type else ''}Original {ct_key.capitalize()}"
                        summarized_button_text = f"Summarized {ct_key.capitalize()}"
                        button_rows.append([
                            InlineKeyboardButton(original_button_text, callback_data=f'original_{ct_key}|{patent.id}|{content_type_code}||'),
                            InlineKeyboardButton(summarized_button_text, callback_data=f'summary_{ct_key}|{patent.id}|{content_type_code}||')
                        ])

                if description:
                    patent_text = f'[{escape_text(patent.title_ru)}]({patent_url})\n{escape_text(description)}'
                    patent_text = patent_text[:4096]
                else:
                    patent_text = f'[{escape_text(patent.title_ru)}]({patent_url})\nNo description available.'

                button_rows.append([InlineKeyboardButton("Summarized All", callback_data=f'summary_all|{patent.id}|{content_type_code}||')])
                button_rows.append([InlineKeyboardButton("Find Similar Patents", callback_data=f'find_similar|{patent.id}')])

                reply_markup = InlineKeyboardMarkup(button_rows)
                await reply_to.reply_text(patent_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True, reply_markup=reply_markup)

            buttons = []

            if offset > 0:
                buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'page_nav|prev_page|{offset - limit}'))
            if search_patent_response.total > offset + limit:
                buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f'page_nav|next_page|{offset + limit}'))

            reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
            await reply_to.reply_text(f"Page: {offset // limit + 1}", reply_markup=reply_markup)


@with_db_connection
async def start_command(update: Update, context: CallbackContext, connection) -> None:
    id = await upsert_user(connection, update.effective_user)
    await update.message.reply_text(escape_text('Welcome! Use `/search языковая модель` for example to search for patents'), parse_mode=ParseMode.MARKDOWN_V2)


@with_db_connection
async def search_command(update: Update, context: CallbackContext, connection) -> int:
    id = await upsert_user(connection, update.effective_user)
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Please enter search query: ")
        return SEARCH_QUERY
    else:
        await create_tg_user_search_query(connection, update.effective_user.id, query, 0)
        await search(query, update, context, from_callback_query=False)
        return ConversationHandler.END


@with_db_connection
async def search_input(update: Update, context: CallbackContext, connection) -> int:
    user_input = update.message.text
    await create_tg_user_search_query(connection, update.effective_user.id, user_input, 0)
    await search(user_input, update, context, from_callback_query=False)
    return ConversationHandler.END


async def search_similar_patents(patent_id, update: Update, context: CallbackContext, limit=10, offset=0):
    reply_to = update.callback_query.message if update.callback_query else update.message

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{RASPATENT_SCRAPER_URL}/rospatent_scraper/title_ru/{patent_id}"
        ) as title_response:
            patent_title = await title_response.json()
            patent_url = f'https://searchplatform.rospatent.gov.ru/doc/{patent_id}'
            await reply_to.reply_text(f"Searching similar patents for [{escape_text(patent_title)}]({patent_url})", parse_mode=ParseMode.MARKDOWN_V2)

        async with session.get(
            f"{RASPATENT_SCRAPER_URL}/rospatent_scraper/search_similar?id={patent_id}&limit={limit}&offset={offset}"
        ) as response:
            result_json = await response.json()
            search_patent_response = SearchPatentResponse.validate(result_json)
            await reply_to.reply_text(f"Total patents: {search_patent_response.total}")
            for patent in search_patent_response.patents:
                patent_url = f'https://searchplatform.rospatent.gov.ru/doc/{patent.id}'
                content_types = {'snippet': 'snippet_ru', 'abstract': 'abstract_ru', 'description': 'description_ru'}
                selected_content_type = None
                button_rows = []
                similarity_info = f'Similarity: {patent.similarity:.5f}, Norm: {patent.similarity_norm:.5f}'
                similarity_code = f'{patent.similarity:.5f}|{patent.similarity_norm:.5f}'

                for ct_key, ct_value in content_types.items():
                    if getattr(patent, ct_value):
                        if selected_content_type is None:
                            selected_content_type = ct_key
                            description = getattr(patent, ct_value)
                            break

                content_type_code = ''.join([ct_key[0] for ct_key, ct_value in content_types.items() if getattr(patent, ct_value)])
                for ct_key, ct_value in content_types.items():
                    if getattr(patent, ct_value):
                        original_button_text = f"{'🔵 ' if ct_key == selected_content_type else ''}Original {ct_key.capitalize()}"
                        summarized_button_text = f"Summarized {ct_key.capitalize()}"
                        button_rows.append([
                            InlineKeyboardButton(original_button_text, callback_data=f'original_{ct_key}|{patent.id}|{content_type_code}|{similarity_code}|'),
                            InlineKeyboardButton(summarized_button_text, callback_data=f'summary_{ct_key}|{patent.id}|{content_type_code}|{similarity_code}|')
                        ])

                if description:
                    patent_text = f'[{escape_text(patent.title_ru)}]({patent_url})\n{escape_text(similarity_info)}\n{escape_text(description)}'
                    patent_text = patent_text[:4096]
                else:
                    patent_text = f'[{escape_text(patent.title_ru)}]({patent_url})\n{escape_text(similarity_info)}No description available.'

                button_rows.append([InlineKeyboardButton("Summarized All", callback_data=f'summary_all|{patent.id}|{content_type_code}|{similarity_code}|')])
                button_rows.append([InlineKeyboardButton("Find Similar Patents", callback_data=f'find_similar|{patent.id}')])

                reply_markup = InlineKeyboardMarkup(button_rows)
                await reply_to.reply_text(patent_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True, reply_markup=reply_markup)

            buttons = []
            if offset > 0:
                buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f'similar_page_nav|prev_page|{patent_id}|{offset - limit}'))
            if search_patent_response.total > offset + limit:
                buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f'similar_page_nav|next_page|{patent_id}|{offset + limit}'))

            reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
            await reply_to.reply_text(f"Page: {offset // limit + 1}", reply_markup=reply_markup)


@with_db_connection
async def pagination_handler(update: Update, context: CallbackContext, connection) -> int:
    query = update.callback_query
    print(f'{query.data}')
    await query.answer()
    _, action, new_offset = query.data.split('|')
    new_offset = int(new_offset)

    search_text = await get_latest_search_query(connection, update.effective_user.id)
    if search_text:
        await create_tg_user_search_query(connection, update.effective_user.id, search_text, new_offset)
        await search(search_text, update, context, offset=new_offset, from_callback_query=True)
        return PAGE_NAVIGATION
    else:
        await update.message.reply_text("No recent search query found. Please start a new search.")
        return ConversationHandler.END


async def similar_patents_pagination_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    _, action, patent_id, new_offset = query.data.split('|')
    new_offset = int(new_offset)
    await search_similar_patents(patent_id, update, context, offset=new_offset)
    return SIMILAR_PAGE_NAVIGATION


async def similar_patents_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    _, patent_id = query.data.split('|')
    await search_similar_patents(patent_id, update, context)


async def summarize_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    print(f"{data=}")
    action, patent_id, available_types, similarity, similarity_norm, *extra_values = data.split('|')
    similarity = float(similarity) if similarity else None
    similarity_norm = float(similarity_norm) if similarity_norm else None

    available_content_types = {
        's': 'snippet',
        'a': 'abstract',
        'c': 'claims',
        'd': 'description'
    }

    section = action.split('_')[1]
    if action.startswith('summary_all'):
        endpoint = f"/giga_chat/all_summary"
        current_selection = 'summary_all'
    elif action.startswith('original'):
        endpoint = f"/giga_chat/{section}_original"
        current_selection = 'original'
    elif action.startswith('summary'):
        endpoint = f"/giga_chat/{section}_summary"
        current_selection = 'summary'
    else:
        await query.answer("Invalid action")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{GIGA_CHAT_API_URL}{endpoint}?patent_id={patent_id}",
        ) as response:
            title, content = await response.json()
            patent_url = f'https://searchplatform.rospatent.gov.ru/doc/{patent_id}'
            if similarity and similarity_norm:
                similarity_info = f'Similarity: {similarity:.5f}, Norm: {similarity_norm:.5f}'
                patent_text = f'[{escape_text(title)}]({patent_url})\n{escape_text(similarity_info)}\n{escape_text(content)}'
                similarity_code = f'{similarity:.5f}|{similarity_norm:.5f}'
            else:
                patent_text = f'[{escape_text(title)}]({patent_url})\n{escape_text(content)}'
                similarity_code = '|'
            patent_text = patent_text[:4096]

            button_rows = []

            for ct_key in available_types:
                ct_value = available_content_types[ct_key]
                original_button_text = f"{'🔵' if current_selection == 'original' and ct_value == section else ''} Original {ct_value.capitalize()}"
                summarized_button_text = f"{'🔵' if current_selection == 'summary' and ct_value == section else ''} Summarized {ct_value.capitalize()}"
                button_rows.append([
                    InlineKeyboardButton(original_button_text, callback_data=f'original_{ct_value}|{patent_id}|{available_types}|{similarity_code}|'),
                    InlineKeyboardButton(summarized_button_text, callback_data=f'summary_{ct_value}|{patent_id}|{available_types}|{similarity_code}|')
                ])

            summarized_all_button_text = f"{'🔵' if current_selection == 'summary_all' else ''} Summarized All"
            button_rows.append([InlineKeyboardButton(summarized_all_button_text, callback_data=f'summary_all|{patent_id}|{available_types}|{similarity_code}|')])
            button_rows.append([InlineKeyboardButton("Find Similar Patents", callback_data=f'find_similar|{patent_id}')])
            reply_markup = InlineKeyboardMarkup(button_rows)

            await query.edit_message_text(patent_text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True, reply_markup=reply_markup)


class PatentCluster(BaseModel):
    patent_id: str
    title: str


class Cluster(BaseModel):
    title: str
    patents: List[PatentCluster]
