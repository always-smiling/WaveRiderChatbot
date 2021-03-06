#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Main Bot Class

import json
import os
import numpy as np
import requests
import RequestSender
from settings import settings
import telebot
import logging
from InfoToMusic import InfoToMusic
from poster import poster
from image_processing import ImageProcessor
from TextMatcher import TextModels
from TextMatcher import TextProcessing
import traceback


class MusicBot:
    def __init__(self):
        # Bot initialization
        self.config = settings()
        self.bot = telebot.TeleBot(self.config.bot_token)
        self.users = self.read_users(self.config.users_name)

        self.infoProcessors = {}

        self.image_processor = ImageProcessor(self.config.cnn_style_model, self.config.cnn_style_pretrained,
                                              self.config.cnn_style_mean)

        # Logger initialization
        self.logger = logging.getLogger('BotLogger')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(self.config.log)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        self.stat_log = logging.getLogger('BotStatisticLogger')
        self.stat_log.setLevel(logging.DEBUG)
        fh_stat = logging.FileHandler(self.config.statistic_log)
        fh_stat.setFormatter(formatter)
        self.stat_log.addHandler(fh_stat)

        self.statistics = {'unique_users': [], 'requests': 0, 'vk': 0}

        self.rs = RequestSender.RequestSender()
        self.allLyrics = self.rs.getAllLyricsByStyles(self.rs.getAllStyles())

        # self.logger.info('Translating all lyrics...')
        # for currSongId in self.allLyrics.keys():  # preprocessing will be done in text_dict_to_vec_dict
        #     song_name_translated = self.textModels.preprocess_sentence(self.allLyrics[currSongId][0])
        #     song_text_translated = self.textModels.preprocess_sentence(self.allLyrics[currSongId][1])
        #     self.allLyrics[currSongId] = song_name_translated, song_text_translated

        textModels = TextModels(self.config.w2vec_model, self.config.w2vec_dict, self.config.eng_rus_dict)

        self.logger.info('Transform all lyrics to vectors...')
        self.text_processor = TextProcessing(textModels)
        self.text_processor.text_dict_to_vec_dict(self.allLyrics)

        self.logger.info('Bot init done')

        # Bot messages
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.bot.send_message(chat_id=message.chat.id,
                                  text='Привет, {0} {1}!\nТебе нужно что-то запостить?\nЯ подберу подходящую музыку {2} под пост и опубликую его для тебя в vk.\n'
                                       'Я могу работать как с текстом, так и с фотографиями. Просто отправь мне всё необходимое.\n\n'
                                  .format(message.from_user.first_name.encode('utf-8'), '\xE2\x9C\x8B', '\xF0\x9F\x8E\xB6'))

        @self.bot.message_handler(commands=['help'])
        def help(message):
            self.bot.send_message(chat_id=message.chat.id,
                                  text='Я подберу для тебя музыку {0}, подходящую под загруженную фотографию или текст. '
                                       'Уточню результат, если потребуется. Загружу найденную песню, '
                                       'а также смогу опубликовать сгенерированный пост на твоей старнице в VK.'
                                  .format('\xF0\x9F\x8E\xA7'))

        @self.bot.message_handler(func=lambda message: True, content_types=['text'])
        def parse_message(message):
            # users_id = self.read_users(self.config.users_token)
            # strToFind = 'https:.+access_token=(.+)\&expires_in=.+'

            try:

                if u"Опубликовать в VK" == message.text:
                    self.logger.info('User %s: VK Publication request' % message.chat.id)
                    if not usersClass.findUser(chatId=message.chat.id):
                        link = r"https://oauth.vk.com/authorize?client_id={}&display=mobile&scope=wall,offline," \
                                    r"audio,photos&redirect_uri={}&response_type=code&v=5.53&state={}".format(
                            self.config.id_vkapi, self.config.set_code_URL, message.chat.id)
                        keyboard = telebot.types.InlineKeyboardMarkup()
                        url_button = telebot.types.InlineKeyboardButton(text="Перейти в VK", url=link)
                        keyboard.add(url_button)
                        self.bot.send_message(chat_id=message.chat.id,
                                              text='Прости {0}, но я не смогу обновить твою стену, '
                                                   'пока ты не пришлешь мне текст из адресной строки, '
                                                   'после перехода по ссылке:'
                                              .format('\xF0\x9F\x98\x94'), reply_markup=keyboard)
                        usersClass.getToken(message.chat.id)

                        if not usersClass.findUser(message.chat.id):
                            self.bot.send_message(chat_id=message.chat.id,
                                                  text='Не могу получить токен. Попробуй повторить публикацию')
                        else:
                            self.bot.send_message(chat_id=message.chat.id,
                                                  text='Спасибо за авторизацию. Публикую твой пост в VK.')

                            music_name = self.infoProcessors[message.chat.id].current_song_name
                            photo_name = self.infoProcessors[message.chat.id].imgFileName
                            text = self.infoProcessors[message.chat.id].userText

                            usersClass.post(pathToMusic=music_name, pathToImage=photo_name, text=text)
                            self.infoProcessors[message.chat.id].clear_all()
                            self.bot.send_message(chat_id=message.chat.id,
                                                  text='Отлично! Не будем останавливаться)\n'
                                                       'Отправь мне фотографию или текст.')

                    else:
                        self.bot.send_message(chat_id=message.chat.id, text='Публикую твой пост в VK.')

                        music_name = self.infoProcessors[message.chat.id].current_song_name
                        photo_name = self.infoProcessors[message.chat.id].imgFileName
                        text = self.infoProcessors[message.chat.id].userText

                        usersClass.post(pathToMusic=music_name, pathToImage=photo_name, text=text)
                        self.infoProcessors[message.chat.id].clear_all()
                        self.bot.send_message(chat_id=message.chat.id,
                                              text='Отлично! Не будем останавливаться)\n'
                                                   'Отправь мне фотографию или текст.')

                    self.statistics['vk'] += 1
                    self.stat_log.info('Unique users: %d, Requests number: %d, VK publications: %d' % (
                        len(self.statistics['unique_users']), self.statistics['requests'], self.statistics['vk']))

                elif u"Хочу еще" == message.text:
                    self.logger.info('User %s: One more song request' % message.chat.id)
                    if message.chat.id in self.infoProcessors.keys():
                        if len(self.infoProcessors[message.chat.id].sorted_songs_ids) == 0:
                            self.logger.info('User %s: No relevant songs' % message.chat.id)
                            self.bot.send_message(chat_id=message.chat.id,
                                                  text='К сожалению, больше нет подходящей музыки. Может попробуем еще раз?\n'
                                                       'Отправь мне фотографию или текст.',
                                                  reply_markup=telebot.types.ReplyKeyboardHide())

                        # Send song
                        self.bot.send_message(chat_id=message.chat.id,
                                              text='Один момент, уже подбираю новую песню.')
                        song, file_mp3 = self.infoProcessors[message.chat.id].get_song()
                        self.send_music(message.chat.id, file_mp3, song['track_name'])
                elif u"Отмена" == message.text:
                    self.logger.info('User %s: Cancel request' % message.chat.id)
                    self.bot.send_message(chat_id=message.chat.id,
                                          text='Прости, что не получилось. Может попробуем еще раз?\n'
                                               'Отправь мне фотографию или текст.',
                                          reply_markup=telebot.types.ReplyKeyboardHide())
                    if message.chat.id in self.infoProcessors.keys():
                        self.infoProcessors[message.chat.id].delete_user_data()
                        del self.infoProcessors[message.chat.id]

                else:
                    text = message.text.encode("utf-8")
                    self.logger.info('User %s: Text description from user: %s' % (message.chat.id, text))

                    # Create new InfoToMusic for new chat_id
                    if message.chat.id not in self.infoProcessors.keys():
                        self.logger.info('User %s: Creating new InfoToMusic for user' % message.chat.id)
                        self.infoProcessors[message.chat.id] = InfoToMusic(message.chat.id, self.rs, self.allLyrics,
                                                                           self.text_processor, self.image_processor)

                        if message.chat.id not in self.statistics['unique_users']:
                            self.statistics['unique_users'].append(message.chat.id)
                        self.statistics['requests'] += 1
                        self.stat_log.info('Unique users: %d, Requests number: %d, VK publications: %d' % (
                            len(self.statistics['unique_users']), self.statistics['requests'], self.statistics['vk']))

                    elif self.infoProcessors[message.chat.id].userText:
                        self.logger.info('User %s: Creating new post' % message.chat.id)
                        self.bot.send_message(chat_id=message.chat.id,
                                              text='Отлично! Начнем заново!', reply_markup=self.generate_markup())
                        self.infoProcessors[message.chat.id].clear_all()
                        # self.infoProcessors[message.chat.id].imgFileName = None

                    self.infoProcessors[message.chat.id].userText = text
                    if len(self.infoProcessors[message.chat.id].relevantSongs) == 0:
                        self.infoProcessors[message.chat.id].relevantSongs = self.allLyrics

                    try:
                        self.bot.send_message(chat_id=message.chat.id,
                                              text='Один момент, уже подбираю песню под введенный текст.')
                        self.infoProcessors[message.chat.id].process()

                        # Send song
                        song, file_mp3 = self.infoProcessors[message.chat.id].get_song()
                        self.send_music(message.chat.id, file_mp3, song['track_name'])
                    except:
                        self.logger.error('User %s: Catch exception in user text processing' % message.chat.id)
                        self.bot.send_message(chat_id=message.chat.id,
                                              text='Возникла ошибка при обработке текста. Может попробуем еще раз?\n'
                                                   'Отправь мне фотографию или текст.',
                                              reply_markup=telebot.types.ReplyKeyboardHide())
                        self.infoProcessors[message.chat.id].delete_user_data()
                        del self.infoProcessors[message.chat.id]

            except:
                self.logger.exception('User %s: Catch exception in parse_message(). Bot failed' % message.chat.id)
                self.bot.send_message(chat_id=message.chat.id,
                                      text='Возникла ошибка. Может попробуем еще раз?\n'
                                           'Отправь мне фотографию или текст.',
                                      reply_markup=telebot.types.ReplyKeyboardHide())

        @self.bot.message_handler(func=lambda message: True, content_types=['photo'])
        def get_image(message):
            try:

                self.logger.info('User %s: Image from user' % message.chat.id)
                self.bot.send_chat_action(message.chat.id, "upload_photo")

                # Get biggest photo
                height_list = []
                for ph in message.photo:
                    height_list.append(ph.height)
                photo_ind = np.argmax(height_list)

                file_info = self.bot.get_file(message.photo[photo_ind].file_id)
                photo_file = requests.get(
                    'https://api.telegram.org/file/bot{0}/{1}'.format(self.config.bot_token, file_info.file_path))

                # Create new InfoToMusic for new chat_id
                if message.chat.id not in self.infoProcessors.keys():
                    self.logger.info('User %s: Creating new InfoToMusic for user' % message.chat.id)
                    self.infoProcessors[message.chat.id] = InfoToMusic(message.chat.id, self.rs, self.allLyrics,
                                                                       self.text_processor, self.image_processor)

                    if message.chat.id not in self.statistics['unique_users']:
                        self.statistics['unique_users'].append(message.chat.id)
                    self.statistics['requests'] += 1
                    self.stat_log.info('Unique users: %d, Requests number: %d, VK publications: %d' % (
                        len(self.statistics['unique_users']), self.statistics['requests'], self.statistics['vk']))

                elif self.infoProcessors[message.chat.id].image_seen:
                    self.logger.info('User %s: Creating new post' % message.chat.id)
                    self.bot.send_message(chat_id=message.chat.id,
                                          text='Отлично! Начнем заново!', reply_markup=self.generate_markup())
                    self.infoProcessors[message.chat.id].clear_all()

                # Saving image
                self.infoProcessors[message.chat.id].save_photo(photo_file)
                self.bot.send_message(chat_id=message.chat.id, text='Один момент, уже подбираю песню под твою фотографию.')

                # Filling fields in appropriate InfoToMusic
                try:
                    self.infoProcessors[message.chat.id].process()

                    # Send song
                    song, file_mp3 = self.infoProcessors[message.chat.id].get_song()
                    self.send_music(message.chat.id, file_mp3, song['track_name'])
                except:
                    self.logger.error('User %s: Catch exception in user image processing' % message.chat.id)
                    self.bot.send_message(chat_id=message.chat.id,
                                          text='Возникла ошибка при обработке картинки. Может попробуем еще раз?\n'
                                               'Отправь мне фотографию или текст.',
                                          reply_markup=telebot.types.ReplyKeyboardHide())

                    self.infoProcessors[message.chat.id].delete_user_data()
                    del self.infoProcessors[message.chat.id]

            except:
                self.logger.exception('User %s: Catch exception in parse_message(). Bot failed' % message.chat.id)
                self.bot.send_message(chat_id=message.chat.id,
                                      text='Возникла ошибка. Может попробуем еще раз?\n'
                                           'Отправь мне фотографию или текст.',
                                      reply_markup=telebot.types.ReplyKeyboardHide())

    def send_music(self, user_id, file_mp3, title):
        self.bot.send_chat_action(user_id, 'upload_audio')
        with open(file_mp3, 'rb') as audio:
            self.bot.send_audio(user_id, audio, title='%s' % title, timeout=1000, reply_markup=self.generate_markup())

    @staticmethod
    def generate_markup():
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Опубликовать в VK')
        markup.add('Хочу еще')
        markup.add('Отмена')
        return markup

    @staticmethod
    def read_users(pathToBase=''):
        res = {}
        if os.path.isfile(pathToBase):
            with open(pathToBase, 'r') as base:
                res = json.loads(base.read())
        return res

    def process(self):
        self.bot.polling(none_stop=True)


if __name__ == '__main__':
    Bot = MusicBot()
    usersClass = poster()
    Bot.process()
