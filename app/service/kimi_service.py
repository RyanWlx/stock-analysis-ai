from app.config.kimi_config import client as kimiClient
import pandas as pd

def getStockStorageDoc():
	completion = kimiClient.chat.completions.create(
		model = "moonshot-v1-128k",
		messages = [
			# {"role": "assistant", "content": "你是 Kimi，你更擅长中文文章内容生成。你会得到一段购买或者卖出股票的决策要求，你可以随时把网址或者互联网上的文章作为参考，为我生成出合理的理由支撑我的买入或者卖出行为，需要有3到5点理由和总结。"},
			# {"role": "user", "content": "帮我写一段“贵州茅台”股票的买入推荐理由，需要有买入的支撑观点，这段描述600字以内，这段描述末尾明确是买入观点；撰写内容的呈现形式是：基于对“贵州茅台”的研究，建议买入，主要原因是：总结的理由,该理由必须包含\"公司基本业务信息\"和\"数据支撑\";原因细则罗列之前先对原因做个总结；综上因素，完成这篇稿子"}
			{"role": "assistant","content": "你是 Kimi，你更擅长中文文章内容生成。帮我写一段“贵州茅台”股票的买入推荐理由，需要有买入的支撑观点，这段描述600字以内，这段描述末尾明确是买入观点；撰写内容的呈现形式是：基于对“贵州茅台”的研究，建议买入，主要原因是：总结的理由,该理由必须包含\"公司基本业务信息\"和\"数据支撑\";原因细则罗列之前先对原因做个总结；综上因素，完成这篇稿子"},
			{"role": "user", "content": "贵州茅台-买入"}
		],
		temperature = 0.3,
	)
	print(completion.choices[0].message)
	return completion.choices[0].message

#根据文字生成word文档


#读取excel原始数据
def getDataSource():
	# 读取Excel文件
	df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
	print(df['代码'])
	return df