from datetime import datetime


def format_date_with_microseconds(time_string):
    time_format = '%Y-%m-%d %H:%M:%S'
    # 解析时间字符串为 datetime 对象
    parsed_time = datetime.strptime(time_string, time_format)

    # 添加微秒部分 (例如，添加 0 微秒)
    time_with_microseconds = parsed_time.replace(microsecond=0)

    # 将 datetime 对象转换回带微秒的字符串格式
    time_string_with_microseconds = time_with_microseconds.strftime('%Y-%m-%d %H:%M:%S.%f')

    return time_string_with_microseconds