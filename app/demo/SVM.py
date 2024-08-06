from sklearn import svm
import DC

if __name__ == '__main__':
    stock = '002049.SZ'
    dc = DC.data_collect(stock, '2010-01-01', '2024-07-01')
    train = dc.data_train
    target = dc.data_target
    test_case = [dc.test_case]
    model = svm.SVC()               # 建模
    model.fit(train, target)        # 训练
    ans2 = model.predict(test_case) # 预测
    # 输出对2024-07-01的涨跌预测，1表示涨，0表示不涨。
    print(ans2[0])
    model = svm.SVR()               # 建模
    model.fit(train, target)        # 训练
    ans3 = model.predict(test_case) # 预测
    # 输出对2024-07-01的涨跌预测，数值大小代表相关性。
    print(ans3[0])


