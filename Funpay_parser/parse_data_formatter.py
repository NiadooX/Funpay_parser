import constants as ct
import json
import os


def main():
    if not os.path.exists(ct.PARSE_DATA_FORMATTED_FOLDER):
        os.mkdir(ct.PARSE_DATA_FORMATTED_FOLDER)

    parsed_categories_list = os.listdir(ct.PARSE_DATA_FOLDER)
    input_msg = 'Выберите категорию, которую вы хотите отформаттировать.'
    input_dict = {}
    count = 1
    for parsed_category in parsed_categories_list:
        input_dict[count] = parsed_category
        input_msg += f' {count} - {parsed_category}.'
        count += 1
    answer = int(input(input_msg + '\n'))
    assert answer in input_dict.keys()
    to_format_category_path = input_dict[answer]
    json_file_path = f'{ct.PARSE_DATA_FOLDER}{os.sep}{to_format_category_path}'
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(fp=f)
    price_range = list(map(lambda x: int(x), input('Выберите диапазон цен funpay.com в формате (min max (через пробел)) в рублях.\n').split()))
    assert len(price_range) == 2
    answer_sort = int(input('Отсортировать по 1 - примерной цене steamid.pro, 2 - цене funpay.com, 3 - примерному профиту.\n'))
    allow_answers = [1, 2, 3]
    assert answer_sort in allow_answers
    answer_sort_order = int(input('Порядок сортировки по 1 - возрастанию, 2 - убыванию.\n'))
    allow_answers_order = [1, 2]
    assert answer_sort_order in allow_answers_order

    data_filtered = list(filter(lambda x: price_range[0] <= int(x['funpay_acc_price'].rstrip('₽')) <= price_range[1], data))
    if answer_sort == 1:
        if answer_sort_order == 2:
            data_result = list(sorted(data_filtered, key=lambda x: int(x['acc_price']['acc_price_rub'].rstrip('₽')), reverse=True))
        else:
            data_result = list(sorted(data_filtered, key=lambda x: int(x['acc_price']['acc_price_rub'].rstrip('₽'))))
    elif answer_sort == 2:
        if answer_sort_order == 2:
            data_result = list(sorted(data_filtered, key=lambda x: int(x['funpay_acc_price'].rstrip('₽')), reverse=True))
        else:
            data_result = list(sorted(data_filtered, key=lambda x: int(x['funpay_acc_price'].rstrip('₽'))))
    elif answer_sort == 3:
        if answer_sort_order == 2:
            data_result = list(sorted(data_filtered, key=lambda x: int(x['profit'].rstrip('₽')), reverse=True))
        else:
            data_result = list(sorted(data_filtered, key=lambda x: int(x['profit'].rstrip('₽'))))

    json_file_formatted_path = f'{ct.PARSE_DATA_FORMATTED_FOLDER}{os.sep}{json_file_path.rstrip('.json').split(os.sep)[1]}_formatted.json'

    with open(json_file_formatted_path, 'w', encoding='utf-8') as f_result:
        json.dump(fp=f_result, obj=data_result, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()
