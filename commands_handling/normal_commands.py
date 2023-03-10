import random as rd
import asyncio
import json
from datetime import datetime, timedelta
from typing import Union, Tuple

import fbchat
from forex_python.converter import CurrencyRates, RatesNotAvailableError
from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException, NotValidPayload
from dataclasses import dataclass

from .logger import logger
from .. import getting_and_editing_files, page_parsing
from .bot_actions import BotActions
from ..sql import handling_group_sql


SETABLE_COLORS = fbchat._threads.SETABLE_COLORS
currency_converter = CurrencyRates()
questions = []
with open("Bot/data/questions.txt") as file:
    for i in file.readlines():
        questions.append(i)


HELP_MESSAGE = """π πππππππ π
!help, !strona, !wersja, !wsparcie, !tworca, !id, !koronawirus, !koronawiruspl, !mem, !luckymember, !ruletka, !pogoda, !nick, !everyone, !utrudnieniawawa, !utrudnienialodz, !moneta, !waluta, !kocha, !banan, !tekst , !stan , !tablica, !pytanie, !essa, !flagi
π πππππππππ πππππππ ππ πππππ ππππππ πππ π
!szukaj, !tlumacz, !miejski, !film, !tvpis, !disco, !powitanie, !nowyregulamin, !regulamin, !zdjecie, !play, !cena, !sstats, !say
π° πππππππ ππ πππ ππππππ (ππ¨π πππ¨π’π§π¬π² π§π’π π¬π π©π«ππ°ππ³π’π°π π’ π§π’π ππ π¬π’π π’ππ‘ π°π²π©Επππ’π)π° 
!register, !daily, !top, !bal, !bet, !zdrapka, !tip, !jackpot, !jackpotbuy, !duel, !email, !kod, !profil, !osiagniecia, !sklep, !slots
"""

LINK_TO_MY_FB_ACCOUNT_MESSAGE = "π¨βπ» MoΕΌesz do mnie (twΓ³rcy) napisaΔ na: https://www.facebook.com/dogson420"

SUPPORT_INFO_MESSAGE = """π§§π°π πππ¬π₯π’ ππ‘πππ¬π³ π°π¬π©π¨π¦π¨π π©π«πππ π§ππ ππ¨π­ππ¦, π¦π¨π³ππ¬π³ π°π²π¬π₯ππ ππ¨π§ππ£π­π. ππ π€ππ³ππ π©π¨π¦π¨π π°π’ππ₯π€π’π ππ³π’ππ€π’ ππ°π§§!
π΄ πππ?π₯ππ‘: paypal.me/DogsonPL
π΄ ππ€π£π©π€ πππ£π π€π¬π: nr konta 22 1140 2004 0000 3002 7878 9413, Jakub Nowakowski
π΄ ππ¨π: wyΕlij kod na pv do !tworca"""

BOT_VERSION_MESSAGE = """β€ππππππππ ππ πππππ ππππππ πππ!β€
π€ πππ«π¬π£π ππ¨π­π: 9.5 + 13.0 pro π€

π§Ύ ππ¬π­ππ­π§π’π¨ ππ¨ ππ¨π­π ππ¨πππ§π¨:
π usuniΔto !koronawirus i !koronawiruspl
Ograniczona iloΕΔ wysyΕanych wiadomoΕci
π mniejszy rozmiar wiadomoΕci
π !sstats
π !essa
π !flagi
"""

download_tiktok = page_parsing.DownloadTiktok()

MARIJUANA_MESSAGES = ["Nie zjarany/a", "Po kilku buszkach", "NiezΕe gastro, zjadΕ/a caΕΔ lodΓ³wkΔ i zamΓ³wiΕ/a dwie duΕΌe pizze",
                      "Pierdoli coΕ o kosmitach", "SΕodko Εpi", "Badtrip :(", "Spierdala przed policjΔ",
                      "Jara wΕaΕnie", "Gotuje wesoΕe ciasteczka", "Mati *kaszle* widaΔ po *kaszle* mnie?",
                      "Mocno wyjebaΕo, nie ma kontaktu", "Jest w swoim Εwiecie", "xDDDDDDDDDDDDDDD", "JD - jest z nim/niΔ dobrze",
                      "Wali wiadro", "WesoΕy", "NajwyΕΌszy/a w pokoju", "MΓ³wi ΕΌe lubi jeΕΊdziΔ na rowerze samochodem",
                      "*kaszlniΔcie*, *kaszlniΔcie*, *kaszlniΔcie*", "Kometa wpadΕa do buzi, poterzny bul"]


@dataclass
class FlagsGame:
    time: datetime.date
    answer: Union[str, list]
    message_id: str


with open("Bot/data/flags.json", "r") as file:
    FLAGS = json.load(file)

flags_game = {}


class Commands(BotActions):
    def __init__(self, client: fbchat.Client, bot_id: str, loop: asyncio.AbstractEventLoop):
        self.get_weather = page_parsing.GetWeather().get_weather
        self.downloading_videos = 0
        self.sending_say_messages = 0
        self.chats_where_making_disco = []
        super().__init__(client, bot_id, loop)

    @logger
    async def send_help_message(self, event: fbchat.MessageEvent):
        await self.send_text_message(event, HELP_MESSAGE)

    @logger
    async def send_link_to_creator_account(self, event: fbchat.MessageEvent):
        await self.send_text_message(event, LINK_TO_MY_FB_ACCOUNT_MESSAGE)

    @logger
    async def send_support_info(self, event: fbchat.MessageEvent):
        await self.send_text_message(event, SUPPORT_INFO_MESSAGE)

    @logger
    async def send_bot_version(self, event: fbchat.MessageEvent):
        await self.send_text_message(event, BOT_VERSION_MESSAGE)

    @logger
    async def send_user_id(self, event: fbchat.MessageEvent):
        await self.send_text_message(event, f"π Twoje id to {event.author.id}")

    @logger
    async def send_webpage_link(self, event: fbchat.MessageEvent):
        await self.send_text_message(event, """π Link do strony www: https://dogson.ovh

Ε»eby poΕΔczyΔ swoje dane z kasynem ΕΌe stronΔ, ustaw w  bocie email za pomocΔ komendy !email, a potem zaΕΓ³ΕΌ konto na stronie bota na ten sam email""")

    @logger
    async def send_weather(self, event: fbchat.MessageEvent):
        city = " ".join(event.message.text.split()[1:])
        if not city:
            message = "π« Po !pogoda podaj miejscowoΕΔ z ktΓ³rej chcesz mieΔ pogodΔ, np !pogoda warszawa"
        else:
            message = await self.get_weather(city)
        await self.send_text_message(event, message)

    @logger
    async def send_public_transport_difficulties_in_warsaw(self, event: fbchat.MessageEvent):
        difficulties_in_warsaw = await page_parsing.get_public_transport_difficulties_in_warsaw()
        await self.send_text_message(event, difficulties_in_warsaw)

    @logger
    async def send_public_transport_difficulties_in_lodz(self, event: fbchat.MessageEvent):
        difficulties_in_lodz = await page_parsing.get_public_transport_difficulties_in_lodz()
        await self.send_text_message(event, difficulties_in_lodz)

    @logger
    async def send_random_meme(self, event: fbchat.MessageEvent):
        meme_path, filetype = await getting_and_editing_files.get_random_meme()
        await self.send_file(event, meme_path, filetype)

    @logger
    async def send_random_film(self, event: fbchat.MessageEvent):
        film_path, filetype = await getting_and_editing_files.get_random_film()
        await self.send_file(event, film_path, filetype)

    @logger
    async def send_random_coin_side(self, event: fbchat.MessageEvent):
        film_path, filetype = await getting_and_editing_files.make_coin_flip()
        await self.send_file(event, film_path, filetype)

    @logger
    async def send_tvpis_image(self, event: fbchat.MessageEvent):
        text = event.message.text[6:]
        image, filetype = await self.loop.run_in_executor(None, getting_and_editing_files.edit_tvpis_image, text)
        await self.send_bytes_file(event, image, filetype)

    @logger
    async def send_tts(self, event: fbchat.MessageEvent):
        if self.sending_say_messages > 8:
            await self.send_text_message(event, "π« Bot obecnie wysyΕa za duΕΌo wiadomoΕci gΕosowych, poczekaj")
        else:
            self.sending_say_messages += 1
            text = event.message.text[4:]
            tts = await self.loop.run_in_executor(None, getting_and_editing_files.get_tts, text)
            await self.send_bytes_audio_file(event, tts)
            self.sending_say_messages -= 1

    @logger
    async def send_yt_video(self, event: fbchat.MessageEvent, yt_link: str):
        if self.downloading_videos > 8:
            await self.send_text_message(event, "π« Bot obecnie pobiera za duΕΌo filmΓ³w. SprΓ³buj ponownie pΓ³ΕΊniej")
        else:
            self.downloading_videos += 1
            link = yt_link
            video, filetype = await self.loop.run_in_executor(None, page_parsing.download_yt_video, link)
            await self.send_bytes_file(event, video, filetype)
            self.downloading_videos -= 1

    @logger
    async def convert_currency(self, event: fbchat.MessageEvent):
        message_data = event.message.text.split()
        try:
            amount = float(message_data[1])
            from_ = message_data[2].upper()
            to = message_data[3].upper()
        except (IndexError, ValueError):
            message = "π‘ UΕΌycie komendy: !waluta iloΕΔ z do - np !waluta 10 PLN USD zamienia 10 zΕoty na 10 dolarΓ³w (x musi byΔ liczbΔ caΕkowitΔ)"
        else:
            try:
                converted_currency = float(currency_converter.convert(from_, to, 1))
            except RatesNotAvailableError:
                message = f"π« Podano niepoprawnΔ walutΔ"
            else:
                new_amount = "%.2f" % (converted_currency*amount)
                message = f"π² {'%.2f' % amount} {from_} to {new_amount} {to}"
        await self.send_text_message(event, message)
        
    @logger
    async def send_random_question(self, event: fbchat.MessageEvent):
        question = rd.choice(questions)
        await self.send_text_message(event, question)

    @logger
    async def send_search_message(self, event: fbchat.MessageEvent):
        thing_to_search = event.message.text.split()[1:]
        if not thing_to_search:
            message = "π‘ Po !szukaj podaj rzecz ktΓ³rΔ chcesz wyszukaΔ"
        else:
            thing_to_search = "_".join(thing_to_search).title()
            if len(thing_to_search) > 50:
                message = "π« Za duΕΌo znakΓ³w"
            else:
                message = await page_parsing.get_info_from_wikipedia(thing_to_search)
        await self.send_text_message(event, message, reply_to_id=event.message.id)

    @logger
    async def send_miejski_message(self, event: fbchat.MessageEvent):
        thing_to_search = event.message.text.split()[1:]
        if not thing_to_search:
            message = "π‘ Po !miejski podaj rzecz ktΓ³rΔ chcesz wyszukaΔ"
        else:
            thing_to_search = "+".join(thing_to_search).title()
            if len(thing_to_search) > 50:
                message = "π« Za duΕΌo znakΓ³w"
            else:
                message = await page_parsing.get_info_from_miejski(thing_to_search)
        await self.send_text_message(event, message, reply_to_id=event.message.id)

    @logger
    async def send_translated_text(self, event: fbchat.MessageEvent):
        try:
            to = event.message.text.split("--")[1].split()[0]
            text = " ".join(event.message.text.split()[2:])
        except IndexError:
            to = "pl"
            text = " ".join(event.message.text.split()[1:])

        if not text or len(text) > 3000:
            translated_text = """π‘ Po !tlumacz napisz co chcesz przetΕumaczyΔ, np !tlumacz siema. Tekst moΕΌe mieΔ maksymalnie 3000 znakΓ³w
MoΕΌesz tekst przetΕumaczyΔ na inny jΔzyk uΕΌywajΔΔ --nazwa_jezyka, np !tlumacz --english siema"""
        else:
            try:
                translated_text = GoogleTranslator("auto", to).translate(text)
            except LanguageNotSupportedException:
                translated_text = f"π« {to} - nie moge znaleΕΊΔ takiego jΔzyka, sprΓ³buj wpisaΔ peΕnΔ nazwΔ jΔzyka"
            except NotValidPayload:
                translated_text = "π« Nie moΕΌna przetΕumaczyΔ tego tekstu"

        if not translated_text:
            translated_text = "π« Nie moΕΌna przetΕumaczyΔ znaku ktΓ³ry zostaΕ podany"
        await self.send_text_message(event, translated_text, reply_to_id=event.message.id)

    @logger
    async def send_google_image(self, event: fbchat.MessageEvent):
        search_query = event.message.text.split()[1:]
        if not search_query:
            await self.send_text_message(event, "π‘ Po !zdjecie napisz czego chcesz zdjΔcie, np !zdjecie pies",
                                         reply_to_id=event.message.id)
        else:
            search_query = "%20".join(search_query)
            if len(search_query) > 100:
                await self.send_text_message(event, "π« Podano za dΕugΔ fraze", reply_to_id=event.message.id)
            else:
                image = await page_parsing.get_google_image(search_query)
                await self.send_bytes_file(event, image, "image/png")

    @logger
    async def send_tiktok(self, event: fbchat.MessageEvent):
        self.downloading_videos += 1
        for i in event.message.text.split():
            if i.startswith("https://vm.tiktok.com/"):
                video = await download_tiktok.download_tiktok(i)
                try:
                    await self.send_bytes_file(event, video, "video/mp4")
                except fbchat.HTTPError:
                    await self.send_text_message(event, "π« Facebook zablokowaΕ wysΕanie tiktoka, sprΓ³buj jeszcze raz",
                                                 reply_to_id=event.message.id)
                break
        self.downloading_videos -= 1

    @logger
    async def send_spotify_song(self, event: fbchat.MessageEvent):
        if self.sending_say_messages > 5:
            await self.send_text_message(event, "π« Bot obecnie pobiera za duΕΌo piosenek, poczekaj sprΓ³buj ponownie za jakiΕ czas",
                                         reply_to_id=event.message.id)
        else:
            song_name = event.message.text.split()[1:]
            if not song_name:
                await self.send_text_message(event, "π‘ Po !play wyΕlij link do piosenki, albo nazwe piosenki. PamiΔtaj ΕΌe wielkoΕΔ liter ma znaczenie, powinna byΔ taka sama jak w tytule piosenki na spotify",
                                             reply_to_id=event.message.id)
                return
            
            song_name = "".join(song_name)
            if len(song_name) > 150:
                await self.send_text_message(event, "π« Za dΕuga nazwa piosenki", reply_to_id=event.message.id)
                return
            
            if "open.spotify.com/playlist" in song_name.lower() or "open.spotify.com/episode" in song_name.lower() or "open.spotify.com/artist" in song_name.lower() or "open.spotify.com/album" in song_name.lower():
                await self.send_text_message(event, "π« MoΕΌna wysyΕaΔ tylko linki do piosenek")
                return

            self.sending_say_messages += 2
            song = await self.loop.run_in_executor(None, page_parsing.download_spotify_song, song_name)
            await self.send_bytes_audio_file(event, song)
            self.sending_say_messages -= 2

    @logger
    async def send_banana_message(self, event: fbchat.MessageEvent):
        mentioned_person = event.message.mentions
        banana_size = rd.randint(-100, 100)
        if mentioned_person:
            mentioned_person_name = event.message.text[8:event.message.mentions[0].length+7]
            message = f"π Banan {mentioned_person_name} ma {banana_size} centymetrΓ³w"
        else:
            message = f"π TwΓ³j banan ma {banana_size} centymetrΓ³w"
        await self.send_text_message(event, message, reply_to_id=event.message.id)

    @logger
    async def send_product_price(self, event: fbchat.MessageEvent):
        item = event.message.text[6:]
        item_query_len = len(item)
        if item_query_len == 0 or item_query_len > 200:
            message = "π‘ Po !cena podaj nazwe przedmiotu (np !cena twoja stara) ktΓ³rego cene chcesz wyszukaΔ, moΕΌe miec max 200 znakΓ³w"
        else:
            message = await page_parsing.check_item_price(item.replace(' ', '+'))
            if not message:
                message = f"π« Nie moΕΌna odnaleΕΊΔ {item} :("
        await self.send_text_message(event, message, reply_to_id=event.message.id)

    @logger
    async def send_song_lyrics(self, event: fbchat.MessageEvent):
        lyrics = "π‘ WyglΔd komendy: !tekst tytuΕ piosenki; twΓ³rca\nPrzykΕad: !lyrics mam na twarzy krew i tym razem nie jest sztuczna; chivas"
        args = event.message.text.split(";")
        try:
            song_name_ = args[0].split()[1:]
            song_name = " ".join(song_name_).replace(" ", "+")
        except IndexError:
            song_name = False
        try:
            creator = args[1].replace(" ", "+")
        except IndexError:
            creator = ""

        if song_name:
            lyrics = await page_parsing.get_lyrics(creator, song_name)
            if not lyrics:
                lyrics = "π’ Nie udaΕo siΔ odnaleΕΊΔ tekstu do piosenki"
            if len(lyrics) > 4000:
                lyrics = lyrics[0:4000]
                lyrics += "\n\n[...] Za dΕugi tekst piosenki (messenger ogranicza wielkoΕΔ wiadomoΕci)"
        await self.send_text_message(event, lyrics, reply_to_id=event.message.id)

    @logger
    async def send_stan_message(self, event: fbchat.MessageEvent):
        mentioned_person = event.message.mentions
        alcohol_level = round(rd.uniform(0, 5), 2)
        marijuana_message = rd.choice(MARIJUANA_MESSAGES)
        if mentioned_person:
            mentioned_person_name = event.message.text[7:event.message.mentions[0].length+6]
            message = f"β¨ Stan {mentioned_person_name}: β¨"
        else:
            message = f"β¨ π§ππΌπ· πππ?π»: β¨"
        message += f"""
π» ππ«π¨π¦π’π₯π: {alcohol_level}β° 
β ππ£ππ«ππ§π’π: {marijuana_message}"""
        await self.send_text_message(event, message, reply_to_id=event.message.id)

    @logger
    async def send_registration_number_info(self, event: fbchat.MessageEvent):
        try:
            registration_number = "".join(event.message.text.split()[1:])
        except IndexError:
            registration_number_info = "π‘ Po !tablica podaj numer rejestracyjny"
        else:
            registration_number_info = await page_parsing.get_vehicle_registration_number_info(registration_number)
        await self.send_text_message(event, registration_number_info)

    @logger
    async def send_play_flags_message(self, event: fbchat.MessageEvent):
        message, reply_to = await play_flags(event)
        await self.send_text_message(event, message, reply_to_id=reply_to)

    @logger
    async def send_essa_message(self, event: fbchat.MessageEvent):
        mentioned_person = event.message.mentions
        essa_percent = rd.randint(0, 100)
        if mentioned_person:
            mentioned_person_name = event.message.text[7:event.message.mentions[0].length + 6]
            message = f"{mentioned_person_name} ma {essa_percent}% essy π€"
        else:
            message = f"Masz  {essa_percent}% essy π€"
        await self.send_text_message(event, message, reply_to_id=event.message.id)

    @logger
    async def make_disco(self, event: fbchat.MessageEvent):
        thread_id = event.thread.id
        if thread_id in self.chats_where_making_disco:
            await self.send_text_message(event, "ππ RozkrΔcam wΕaΕnie imprezΔ")
        else:
            self.chats_where_making_disco.append(event.thread.id)
            for _ in range(12):
                color = rd.choice(SETABLE_COLORS)
                await event.thread.set_color(color)
            self.chats_where_making_disco.remove(thread_id)

    @logger
    async def change_nick(self, event: fbchat.MessageEvent):
        try:
            await event.thread.set_nickname(user_id=event.author.id, nickname=" ".join(event.message.text.split()[1:]))
        except fbchat.InvalidParameters:
            await self.send_text_message(event, "π« Wpisano za dΕugi nick", reply_to_id=event.message.id)


async def play_flags(event: fbchat.MessageEvent) -> Tuple[str, Union[str, None]]:
    answer = flags_game.get(event.thread.id)
    if answer and answer.time + timedelta(minutes=10) > datetime.now():
        country = event.message.text[6:].lower().strip()
        if not country:
            return "π‘ Po !flagi podaj nazwΔ kraju, do ktΓ³rego naleΕΌy ta flaga", answer.message_id

        good_answer = False
        if isinstance(answer.answer, str):
            if country == answer.answer:
                good_answer = True
        else:
            for i in answer.answer:
                if i == country:
                    good_answer = True
                    break
        if good_answer:
            user_points = await handling_group_sql.get_user_flags_wins(event.author.id)
            try:
                user_points += 1
            except TypeError:
                return "π‘ UΕΌyj polecenia !register ΕΌeby mΓ³c siΔ bawiΔ w kasyno. Wszystkie dogecoiny sΔ sztuczne", event.message.id
            else:
                await handling_group_sql.set_user_flags_wins(event.author.id, user_points)
                del flags_game[event.thread.id]
                return f"π Dobra odpowiedΕΊ! Posiadasz juΕΌ {user_points} dobrych odpowiedzi", event.message.id
        else:
            return "π ZΕa odpowiedΕΊ", event.message.id
    flag, answer = rd.choice(list(FLAGS.items()))
    flags_game[event.thread.id] = FlagsGame(datetime.now(), answer, event.message.id)
    return f"Flaga do odgadniΔcia {flag}\nNapisz !flagi nazwa_paΕstwa", None
