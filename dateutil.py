from datetime import datetime


def format_date_with_microseconds(time_string):
    # 尝试解析带微秒的时间字符串
    try:
        time_format_with_microseconds = '%Y-%m-%d %H:%M:%S.%f'
        parsed_time = datetime.strptime(time_string, time_format_with_microseconds)
    except ValueError:
        # 如果失败，尝试解析不带微秒的时间字符串
        time_format_without_microseconds = '%Y-%m-%d %H:%M:%S'
        parsed_time = datetime.strptime(time_string, time_format_without_microseconds)
        # 添加微秒部分 (例如，添加 0 微秒)
        parsed_time = parsed_time.replace(microsecond=0)

    # 将 datetime 对象转换回带微秒的字符串格式
    time_string_with_microseconds = parsed_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    return time_string_with_microseconds


if __name__ == '__main__':
    time_string = '2025-01-09 02:31:03'
    print(format_date_with_microseconds(time_string))