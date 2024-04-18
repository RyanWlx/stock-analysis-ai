import re

# 验证手机号码
def is_valid_phone_number(phone_number):
	pattern = re.compile(r'^1\d{10}$')
	return pattern.match(phone_number) is not None

# 验证密码
def is_valid_password(password):
	pattern = re.compile(r'^[a-zA-Z0-9]{8,20}$')
	return pattern.match(password) is not None

# 验证字符串是否为空
def is_valid_string(string):
	return string is not None and string != ''