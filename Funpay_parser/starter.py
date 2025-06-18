import constants as ct
import os
import json


class Starter:
    config_path = ct.DATA_FOLDER + os.sep + ct.CONFIG_FILE

    @classmethod
    def __configure(cls):
        to_parse_lst = []
        w = input('Введите категорию для парсинга (в точности как на funpay.com) (0 - для остановки): ').strip().lower()
        while w.strip() != '0':
            to_parse_lst.append(w.strip())
            w = input('Введите категорию для парсинга (в точности как на funpay.com) (0 - для остановки): ').strip().lower()
        if not os.path.exists(ct.DATA_FOLDER):
            os.mkdir(ct.DATA_FOLDER)
        with open(cls.config_path, 'w', encoding='utf-8') as cfg:
            data = {'to_parse_lst': to_parse_lst}
            json.dump(fp=cfg, obj=data, indent=4, ensure_ascii=False)
        print('[+] Регистрация успешно завершена!')

    @classmethod
    def __read_config(cls):
        with open(cls.config_path, 'r', encoding='utf-8') as cfg:
            return json.load(fp=cfg)

    @classmethod
    def start(cls):
        if not os.path.exists(ct.DATA_FOLDER) or not os.path.exists(cls.config_path):
            print('[ERROR] Конфиг файл не найден, запускаем регистрацию...')
            cls.__configure()
        return cls.__read_config()